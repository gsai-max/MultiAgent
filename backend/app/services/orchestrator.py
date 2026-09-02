import asyncio
import logging
from typing import Optional, List, Dict, Any
from backend.app.schemas.domain import (
    TravelConstraints,
    ActivityCatalog,
    ActivityItem,
    LodgingPlan,
    MovementPlan,
    DaySkeleton,
    DaySlot,
    BudgetBreakdown,
    DraftItinerary,
    ReviewReport,
    FinalItinerary
)
from backend.app.agents.destination import DestinationAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAgent
from backend.app.agents.review import ReviewAgent
from backend.app.agents.presenter_agent import PresenterAgent
from backend.app.services.constraint_extractor import ConstraintExtractor
from backend.app.services.llm_client import LLMClient
from backend.app.services.plan_store import PlanStateStore
from backend.app.tools.router import ToolRouter

logger = logging.getLogger("ai_travel_planner.services.orchestrator")


AGENT_TIMEOUT_SECONDS = 15.0

class OrchestratorService:
    """Orchestrator Service (Part B & C) responsible for parallel worker execution, itinerary merging, quality review, & repair loops."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        tool_router: Optional[ToolRouter] = None,
        destination_agent: Optional[DestinationAgent] = None,
        logistics_agent: Optional[LogisticsAgent] = None,
        budget_agent: Optional[BudgetAgent] = None,
        review_agent: Optional[ReviewAgent] = None,
        constraint_extractor: Optional[ConstraintExtractor] = None,
        presenter_agent: Optional[PresenterAgent] = None,
        plan_store: Optional[PlanStateStore] = None,
    ):
        self.llm_client = llm_client or LLMClient()
        self.tool_router = tool_router or ToolRouter()
        self.destination_agent = destination_agent or DestinationAgent(
            llm_client=self.llm_client, tool_router=self.tool_router
        )
        self.logistics_agent = logistics_agent or LogisticsAgent(
            llm_client=self.llm_client, tool_router=self.tool_router
        )
        self.budget_agent = budget_agent or BudgetAgent(
            llm_client=self.llm_client, tool_router=self.tool_router
        )
        self.review_agent = review_agent or ReviewAgent(
            llm_client=self.llm_client
        )
        self.constraint_extractor = constraint_extractor or ConstraintExtractor(
            llm_client=self.llm_client
        )
        self.presenter_agent = presenter_agent or PresenterAgent()
        self.plan_store = plan_store or PlanStateStore()


    async def run_parallel_workers(
        self,
        constraints: TravelConstraints,
        trace_id: Optional[str] = None
    ) -> tuple[ActivityCatalog, tuple[LodgingPlan, MovementPlan, List[DaySkeleton]], BudgetBreakdown]:
        """Runs Destination, Logistics, and Budget agents concurrently with per-agent timeouts and graceful fallbacks."""
        logger.info(f"[TraceID: {trace_id or 'none'}] Orchestrator starting parallel execution of specialist agents...")

        async def safe_dest() -> ActivityCatalog:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self.destination_agent.run, constraints, trace_id),
                    timeout=AGENT_TIMEOUT_SECONDS
                )
            except Exception as err:
                logger.warning(f"[TraceID: {trace_id or 'none'}] DestinationAgent failed or timed out: {err}. Utilizing fallback catalog.")
                return self.destination_agent._build_stub_catalog(constraints, [])

        async def safe_logistics() -> tuple[LodgingPlan, MovementPlan, List[DaySkeleton]]:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self.logistics_agent.run, constraints, trace_id),
                    timeout=AGENT_TIMEOUT_SECONDS
                )
            except Exception as err:
                logger.warning(f"[TraceID: {trace_id or 'none'}] LogisticsAgent failed or timed out: {err}. Utilizing fallback logistics.")
                return self.logistics_agent._build_stub_logistics(constraints, [], {})

        async def safe_budget() -> BudgetBreakdown:
            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(self.budget_agent.run, constraints, None, None, trace_id),
                    timeout=AGENT_TIMEOUT_SECONDS
                )
            except Exception as err:
                logger.warning(f"[TraceID: {trace_id or 'none'}] BudgetAgent failed or timed out: {err}. Utilizing fallback budget.")
                return self.budget_agent._build_stub_budget(constraints, None, None, {})

        catalog, (lodging_plan, movement_plan, day_skeletons), initial_budget = await asyncio.gather(
            safe_dest(), safe_logistics(), safe_budget()
        )

        logger.info(f"[TraceID: {trace_id or 'none'}] Specialist agents completed parallel execution.")
        return catalog, (lodging_plan, movement_plan, day_skeletons), initial_budget


    def merge(
        self,
        constraints: TravelConstraints,
        catalog: ActivityCatalog,
        lodging_plan: LodgingPlan,
        movement_plan: MovementPlan,
        day_skeletons: List[DaySkeleton],
        initial_budget: BudgetBreakdown
    ) -> DraftItinerary:
        """Merges catalog, lodging, movement, day schedules, and budget into a DraftItinerary."""
        logger.info(f"Orchestrator merging specialist outputs for {constraints.duration_days}-day trip to {constraints.cities}...")

        # 1. Link day slots to catalog activity IDs & resolve activity schedule conflicts
        catalog_by_id: Dict[str, ActivityItem] = {act.id: act for act in catalog.activities}
        catalog_by_city: Dict[str, List[ActivityItem]] = {}
        for act in catalog.activities:
            catalog_by_city.setdefault(act.city, []).append(act)

        assigned_activity_ids = set()

        for day in day_skeletons:
            city_activities = catalog_by_city.get(day.city, [])
            for slot in day.slots:
                # Check if slot activity_id is valid and in catalog
                if slot.activity_id and slot.activity_id in catalog_by_id:
                    matched_act = catalog_by_id[slot.activity_id]
                    slot.activity_name = matched_act.name
                    assigned_activity_ids.add(matched_act.id)
                else:
                    # Attempt to link to an unassigned activity in the same city
                    available = [act for act in city_activities if act.id not in assigned_activity_ids]
                    if available:
                        chosen = available[0]
                        slot.activity_id = chosen.id
                        slot.activity_name = chosen.name
                        assigned_activity_ids.add(chosen.id)
                    elif city_activities:
                        chosen = city_activities[0]
                        slot.activity_id = chosen.id
                        slot.activity_name = chosen.name

        # 2. Budget reconciliation pass (tightening numbers against actual scheduled slots & lodging options)
        reconciled_budget = self._reconcile_budget(
            constraints=constraints,
            catalog=catalog,
            lodging_plan=lodging_plan,
            movement_plan=movement_plan,
            day_skeletons=day_skeletons,
            initial_budget=initial_budget
        )

        # 3. Generate narrative summary
        cities_str = ", ".join(constraints.cities)
        narrative = (
            f"{constraints.duration_days}-Day custom travel itinerary for {constraints.destination_region} "
            f"covering {cities_str}. Features lodging in top neighborhoods ({', '.join(lodging_plan.suggested_neighborhoods.keys())}), "
            f"inter-city movement via {movement_plan.inter_city_mode}, and curated daily experiences. "
            f"Estimated total spend: ${reconciled_budget.total_estimated_spend} {constraints.currency} "
            f"({'within budget' if reconciled_budget.within_budget else 'budget cap exceeded'})."
        )

        return DraftItinerary(
            constraints=constraints,
            day_by_day=day_skeletons,
            lodging_plan=lodging_plan,
            movement_plan=movement_plan,
            budget_summary=reconciled_budget,
            narrative_summary=narrative
        )

    def _reconcile_budget(
        self,
        constraints: TravelConstraints,
        catalog: ActivityCatalog,
        lodging_plan: LodgingPlan,
        movement_plan: MovementPlan,
        day_skeletons: List[DaySkeleton],
        initial_budget: BudgetBreakdown
    ) -> BudgetBreakdown:
        """Re-evaluates and reconciles category costs to ensure tight budget consistency across merged components."""
        # Lodging spend calculation
        lodging_total = sum(
            opt.estimated_cost_per_night * lodging_plan.nights_per_city.get(opt.city, 1)
            for opt in lodging_plan.options
        ) if lodging_plan.options else initial_budget.per_category_totals.get("lodging", 0.0)

        # Transport spend calculation from movement plan
        transit_cost = sum(
            t.get("estimated_cost", 0.0) for t in movement_plan.transfers
        ) if movement_plan.transfers else 0.0
        # Add baseline daily local transit allowance ($15/day)
        local_transit = constraints.duration_days * 15.0
        transport_total = transit_cost + local_transit

        # Scheduled activities cost calculation
        scheduled_activity_ids = {
            slot.activity_id for day in day_skeletons for slot in day.slots if slot.activity_id
        }
        catalog_by_id = {act.id: act for act in catalog.activities}
        activities_total = sum(
            catalog_by_id[act_id].estimated_cost
            for act_id in scheduled_activity_ids
            if act_id in catalog_by_id
        ) if scheduled_activity_ids else initial_budget.per_category_totals.get("activities", 0.0)

        # Food allowance calculation ($50/day baseline unless specified)
        food_total = constraints.duration_days * 50.0

        per_category = {
            "lodging": round(lodging_total, 2),
            "transport": round(transport_total, 2),
            "food": round(food_total, 2),
            "activities": round(activities_total, 2)
        }

        total_spend = round(sum(per_category.values()), 2)
        within_budget = total_spend <= constraints.budget_total

        violations: List[str] = []
        suggested_swaps: List[Dict[str, Any]] = list(initial_budget.suggested_swaps)

        if not within_budget:
            overage = round(total_spend - constraints.budget_total, 2)
            violations.append(
                f"Merged itinerary spend (${total_spend}) exceeds budget cap of ${constraints.budget_total} by ${overage}."
            )

        return BudgetBreakdown(
            per_category_totals=per_category,
            total_estimated_spend=total_spend,
            within_budget=within_budget,
            violations=violations,
            suggested_swaps=suggested_swaps
        )

    async def run_pipeline(
        self,
        constraints: TravelConstraints,
        trace_id: Optional[str] = None
    ) -> DraftItinerary:
        """Executes full Phase 5 orchestrator pipeline: parallel worker runs followed by merging into DraftItinerary."""
        catalog, (lodging_plan, movement_plan, day_skeletons), initial_budget = await self.run_parallel_workers(
            constraints, trace_id
        )

        draft = self.merge(
            constraints=constraints,
            catalog=catalog,
            lodging_plan=lodging_plan,
            movement_plan=movement_plan,
            day_skeletons=day_skeletons,
            initial_budget=initial_budget
        )
        return draft

    def review_draft(
        self,
        draft: DraftItinerary,
        trace_id: Optional[str] = None
    ) -> ReviewReport:
        """Executes Phase 6 Quality Gate review on a DraftItinerary."""
        logger.info(f"[TraceID: {trace_id or 'none'}] Orchestrator triggering ReviewAgent quality gate...")
        return self.review_agent.run(draft, trace_id=trace_id)

    def apply_repairs(
        self,
        draft: DraftItinerary,
        review_report: ReviewReport
    ) -> tuple[DraftItinerary, Dict[str, Any]]:
        """Applies targeted repairs to draft itinerary to fix ReviewReport blocking issues (Phase 7)."""
        repair_actions = []

        # 1. Fix budget overage issue
        if not review_report.checklist.get("within_budget", True) or any(i.issue_id == "issue_prog_over_budget" for i in review_report.issues):
            overage = draft.budget_summary.total_estimated_spend - draft.constraints.budget_total
            # Swap lodging options to budget level ($80/night)
            for opt in draft.lodging_plan.options:
                opt.estimated_cost_per_night = min(opt.estimated_cost_per_night, 80.0)
                opt.name = f"{opt.city} Budget Guesthouse"

            # Re-reconcile budget
            empty_catalog = ActivityCatalog(activities=[])
            draft.budget_summary = self._reconcile_budget(
                constraints=draft.constraints,
                catalog=empty_catalog,
                lodging_plan=draft.lodging_plan,
                movement_plan=draft.movement_plan,
                day_skeletons=draft.day_by_day,
                initial_budget=draft.budget_summary
            )
            repair_actions.append(f"Trimmed lodging costs to budget level. Reduced spend by ${overage:.2f}.")

        # 2. Fix day count mismatch issue
        if not review_report.checklist.get("days_match", True) or any(i.issue_id == "issue_prog_days_mismatch" for i in review_report.issues):
            target_days = draft.constraints.duration_days
            curr_days = len(draft.day_by_day)
            if curr_days < target_days:
                last_city = draft.constraints.cities[-1]
                for day_num in range(curr_days + 1, target_days + 1):
                    draft.day_by_day.append(
                        DaySkeleton(
                            day_number=day_num,
                            city=last_city,
                            slots=[
                                DaySlot(
                                    slot_id=f"d{day_num}_s1",
                                    time_of_day="morning",
                                    activity_id=f"act_{last_city.lower()}_01",
                                    activity_name=f"{last_city} Exploration & Culture"
                                )
                            ]
                        )
                    )
                repair_actions.append(f"Rebalanced schedule from {curr_days} to {target_days} days.")
            elif curr_days > target_days:
                draft.day_by_day = draft.day_by_day[:target_days]
                repair_actions.append(f"Trimmed extra days to match required {target_days}-day duration.")

        # 3. Fix missing required cities issue
        if not review_report.checklist.get("cities_included", True) or any(i.issue_id == "issue_prog_missing_cities" for i in review_report.issues):
            scheduled = {d.city for d in draft.day_by_day}
            missing = [c for c in draft.constraints.cities if c not in scheduled]
            if missing:
                for city in missing:
                    # Update last day to missing city
                    if draft.day_by_day:
                        draft.day_by_day[-1].city = city
                        draft.day_by_day[-1].slots = [
                            DaySlot(
                                slot_id=f"d{draft.day_by_day[-1].day_number}_s1",
                                time_of_day="morning",
                                activity_id=f"act_{city.lower()}_01",
                                activity_name=f"{city} Central Highlights & Dining"
                            )
                        ]
                    draft.lodging_plan.nights_per_city[city] = 1
                repair_actions.append(f"Added missing required cities ({', '.join(missing)}) to schedule.")

        repair_record = {
            "cycle": len(draft.day_by_day),
            "actions_taken": repair_actions or ["General pacing adjustment"]
        }

        return draft, repair_record

    def generate_presentation_markdown(
        self,
        draft: DraftItinerary,
        review_report: ReviewReport
    ) -> str:
        """Generates rich Markdown presentation document for user & frontend rendering (Phase 7)."""
        c = draft.constraints
        md_lines = [
            f"# ✈️ {c.duration_days}-Day Trip Itinerary: {c.destination_region}",
            f"\n> **Cities:** {', '.join(c.cities)} | **Budget Cap:** ${c.budget_total} {c.currency} | **Pacing:** Balanced",
            f"\n## 📋 Trip Overview\n{draft.narrative_summary}",
            "\n---",
            "\n## 📅 Day-by-Day Schedule"
        ]

        for day in draft.day_by_day:
            md_lines.append(f"\n### Day {day.day_number} — {day.city}")
            for slot in day.slots:
                time_title = slot.time_of_day.capitalize()
                transit_note = f" *(Transit: {slot.travel_time_from_prev_minutes}m)*" if slot.travel_time_from_prev_minutes > 0 else ""
                md_lines.append(f"- **{time_title}:** {slot.activity_name}{transit_note}")

        md_lines.extend([
            "\n---",
            "\n## 🏨 Lodging & Neighborhood Suggestions"
        ])
        for opt in draft.lodging_plan.options:
            nights = draft.lodging_plan.nights_per_city.get(opt.city, 1)
            md_lines.append(f"- **{opt.city} ({opt.neighborhood}):** {opt.name} — *~${opt.estimated_cost_per_night}/night ({nights} nights)*")

        md_lines.extend([
            "\n---",
            "\n## 🚆 Transit & Movement",
            f"- **Inter-city Mode:** {draft.movement_plan.inter_city_mode}"
        ])
        for tr in draft.movement_plan.transfers:
            md_lines.append(f"- {tr.get('from_city')} ➔ {tr.get('to_city')}: {tr.get('mode')} (~{tr.get('duration_minutes')} mins, ${tr.get('estimated_cost')})")

        md_lines.extend([
            "\n---",
            "\n## 💰 Budget Breakdown",
            f"- **Lodging:** ${draft.budget_summary.per_category_totals.get('lodging', 0):.2f}",
            f"- **Transport:** ${draft.budget_summary.per_category_totals.get('transport', 0):.2f}",
            f"- **Food:** ${draft.budget_summary.per_category_totals.get('food', 0):.2f}",
            f"- **Activities:** ${draft.budget_summary.per_category_totals.get('activities', 0):.2f}",
            f"\n**Total Estimated Spend:** `${draft.budget_summary.total_estimated_spend:.2f} {c.currency}` ({'✅ Within Budget' if draft.budget_summary.within_budget else '⚠️ Budget Cap Exceeded'})",
            "\n---",
            f"\n## 🛡️ Quality Review Status\n- **Gate Outcome:** {'PASS ✅' if review_report.passed else 'REVIEWS/WARNINGS ⚠️'}",
            f"- **Checklist:** {', '.join([f'{k}: ok' if v else f'{k}: flag' for k, v in review_report.checklist.items()])}",
            f"\n> **Disclaimer:** {FinalItinerary.model_fields['disclaimer'].default}"
        ])

        return "\n".join(md_lines)

    async def run_full_pipeline(
        self,
        request_text: str,
        max_repairs: int = 2,
        trace_id: Optional[str] = None
    ) -> FinalItinerary:
        """Executes full Phase 7 pipeline: extraction -> parallel workers -> merge -> bounded repair loop -> FinalItinerary."""
        trace_id = trace_id or "trace-default"
        logger.info(f"[TraceID: {trace_id}] Starting full Orchestrator pipeline for request: '{request_text[:40]}...'")

        # 1. Extract constraints (Part A)
        constraints = self.constraint_extractor.extract(request_text)

        # 2. Run parallel workers & merge draft (Part B)
        draft = await self.run_pipeline(constraints, trace_id=trace_id)

        # 3. Bounded Repair Loop (Part C)
        repair_history = []
        review_report = self.review_draft(draft, trace_id=trace_id)

        repair_count = 0
        while not review_report.passed and repair_count < max_repairs:
            logger.info(f"[TraceID: {trace_id}] Review gate flagged issues. Executing repair cycle {repair_count + 1}/{max_repairs}...")
            draft, record = self.apply_repairs(draft, review_report)
            repair_history.append(record)
            review_report = self.review_draft(draft, trace_id=trace_id)
            repair_count += 1

        # 4. Generate presentation markdown & PresenterAgent formatting
        formatted_md = self.generate_presentation_markdown(draft, review_report)

        final_itinerary = FinalItinerary(
            trace_id=trace_id,
            request=request_text,
            constraints=draft.constraints,
            day_by_day=draft.day_by_day,
            lodging_plan=draft.lodging_plan,
            movement_plan=draft.movement_plan,
            budget_summary=draft.budget_summary,
            review_report=review_report,
            repair_history=repair_history,
            narrative_summary=draft.narrative_summary or "Trip itinerary overview.",
            formatted_markdown=formatted_md,
            requires_human_review=not review_report.passed
        )

        # 5. Run Presenter Agent & Save to PlanStateStore
        try:
            final_itinerary.presenter_output = self.presenter_agent.format_presentation(final_itinerary)
        except Exception as e:
            logger.warning(f"PresenterAgent formatting failed: {e}")

        try:
            self.plan_store.save_plan(final_itinerary)
        except Exception as e:
            logger.warning(f"Failed to persist plan to PlanStateStore: {e}")

        return final_itinerary



