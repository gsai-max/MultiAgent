import logging
from typing import Optional, Dict, Any, List
from backend.app.schemas.domain import (
    TravelConstraints,
    BudgetBreakdown,
    LodgingPlan,
    ActivityCatalog
)
from backend.app.services.llm_client import LLMClient
from backend.app.tools.router import ToolRouter

logger = logging.getLogger("ai_travel_planner.agents.budget")

SYSTEM_PROMPT_BUDGET = """
You are the Budget Agent in the AI Travel Planner multi-agent system.
Your job is to calculate expense breakdowns across categories (lodging, transport, food, activities), determine total estimated spend, verify if the plan is within budget, and flag violations or suggest cost-saving swaps.

Instructions:
1. Estimate total costs per category.
2. Sum up total_estimated_spend.
3. Compare against budget_total. Set within_budget = (total_estimated_spend <= budget_total).
4. If over budget, populate violations with clear explanations and suggested_swaps with cheaper alternatives.
5. Return a valid BudgetBreakdown JSON object.
"""


class BudgetAgent:
    """Specialist worker agent for financial breakdown, cap enforcement, and cost swaps (Phase 4c)."""

    def __init__(self, llm_client: Optional[LLMClient] = None, tool_router: Optional[ToolRouter] = None):
        self.llm_client = llm_client or LLMClient()
        self.tool_router = tool_router or ToolRouter()

    def run(
        self,
        constraints: TravelConstraints,
        lodging_plan: Optional[LodgingPlan] = None,
        catalog: Optional[ActivityCatalog] = None,
        trace_id: Optional[str] = None
    ) -> BudgetBreakdown:
        logger.info(f"[TraceID: {trace_id or 'none'}] BudgetAgent running for budget_total: ${constraints.budget_total} {constraints.currency}")

        # Retrieve price band benchmarks for food and activities per city
        price_benchmarks: Dict[str, Any] = {}
        for city in constraints.cities:
            price_benchmarks[city] = {
                "food": self.tool_router.price_band(category="food", city=city, tier="medium", trace_id=trace_id),
                "transport": self.tool_router.price_band(category="transport", city=city, tier="medium", trace_id=trace_id),
                "activities": self.tool_router.price_band(category="activities", city=city, tier="medium", trace_id=trace_id)
            }

        if self.llm_client.is_mock:
            return self._build_stub_budget(constraints, lodging_plan, catalog, price_benchmarks)

        prompt = (
            f"Travel Constraints:\n{constraints.model_dump_json(indent=2)}\n\n"
            f"Lodging Plan:\n{lodging_plan.model_dump_json(indent=2) if lodging_plan else 'None'}\n\n"
            f"Activity Catalog:\n{catalog.model_dump_json(indent=2) if catalog else 'None'}\n\n"
            f"Price Benchmarks:\n{price_benchmarks}"
        )

        budget_breakdown = self.llm_client.extract_structured(
            prompt=prompt,
            response_model=BudgetBreakdown,
            system_prompt=SYSTEM_PROMPT_BUDGET,
            temperature=0.1
        )
        return budget_breakdown

    def _build_stub_budget(
        self,
        constraints: TravelConstraints,
        lodging_plan: Optional[LodgingPlan],
        catalog: Optional[ActivityCatalog],
        price_benchmarks: Dict[str, Any]
    ) -> BudgetBreakdown:
        """Deterministic stub budget builder for mock execution & unit tests."""
        duration = constraints.duration_days

        # 1. Lodging total
        lodging_total = 0.0
        if lodging_plan and lodging_plan.options:
            for opt in lodging_plan.options:
                nights = lodging_plan.nights_per_city.get(opt.city, 2)
                lodging_total += opt.estimated_cost_per_night * nights
        else:
            lodging_total = 140.0 * (duration - 1)

        # 2. Transport total (inter-city Shinkansen + daily subway)
        transport_total = 260.0 if len(constraints.cities) > 1 else 80.0

        # 3. Food total (e.g., $50/day)
        food_total = 50.0 * duration

        # 4. Activities total
        activities_total = 0.0
        if catalog and catalog.activities:
            activities_total = sum(act.estimated_cost for act in catalog.activities)
        else:
            activities_total = 150.0

        per_category = {
            "lodging": round(lodging_total, 2),
            "transport": round(transport_total, 2),
            "food": round(food_total, 2),
            "activities": round(activities_total, 2)
        }

        total_spend = round(sum(per_category.values()), 2)
        within_budget = total_spend <= constraints.budget_total

        violations: List[str] = []
        suggested_swaps: List[Dict[str, Any]] = []

        if not within_budget:
            overage = round(total_spend - constraints.budget_total, 2)
            violations.append(
                f"Total estimated spend (${total_spend}) exceeds budget cap of ${constraints.budget_total} by ${overage}."
            )
            suggested_swaps.append({
                "category": "lodging",
                "original": "Central Hotel",
                "replacement": "Budget Ryokan / Guesthouse",
                "potential_savings": round(overage + 50.0, 2)
            })

        return BudgetBreakdown(
            per_category_totals=per_category,
            total_estimated_spend=total_spend,
            within_budget=within_budget,
            violations=violations,
            suggested_swaps=suggested_swaps
        )
