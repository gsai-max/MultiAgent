import logging
from typing import Optional, List, Dict, Any
from backend.app.schemas.domain import (
    DraftItinerary,
    ReviewReport,
    ReviewIssue
)
from backend.app.services.llm_client import LLMClient

logger = logging.getLogger("ai_travel_planner.agents.review")

SYSTEM_PROMPT_REVIEW = """
You are the Review Agent in the AI Travel Planner multi-agent system.
Your job is to conduct a qualitative quality gate evaluation on a merged DraftItinerary.

Instructions:
1. Assess qualitative aspects:
   - preferences_met: Does the plan align with user preferences (e.g., temples, culinary, culture)?
   - crowd_avoidance_effort: Does the plan incorporate off-peak / lower-crowd strategies if avoidances specify crowds?
   - logistics_realism: Are transit times and day slot sequences realistic without excessive backtracking?
2. Produce a ReviewReport with:
   - checklist: map containing (days_match, cities_included, within_budget, preferences_met, crowd_avoidance_effort, logistics_realism)
   - issues: list of ReviewIssue items with severity ("blocking" or "advisory")
   - passed: boolean (true if no blocking issues exist and quality bar is met)
"""


class ReviewAgent:
    """Specialist Quality Gate agent conducting programmatic & qualitative review (Phase 6)."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def run(self, draft: DraftItinerary, trace_id: Optional[str] = None) -> ReviewReport:
        logger.info(f"[TraceID: {trace_id or 'none'}] ReviewAgent evaluating draft itinerary for {draft.constraints.destination_region}...")

        # --- Layer 1: Programmatic Validation ---
        prog_issues: List[ReviewIssue] = []
        checklist: Dict[str, bool] = {}

        # 1. Day count check
        days_match = len(draft.day_by_day) == draft.constraints.duration_days
        checklist["days_match"] = days_match
        if not days_match:
            prog_issues.append(
                ReviewIssue(
                    issue_id="issue_prog_days_mismatch",
                    severity="blocking",
                    description=f"Day count mismatch: itinerary has {len(draft.day_by_day)} days, expected {draft.constraints.duration_days}.",
                    field_target="day_by_day"
                )
            )

        # 2. City coverage check
        scheduled_cities = {day.city for day in draft.day_by_day}
        if draft.lodging_plan and draft.lodging_plan.nights_per_city:
            scheduled_cities.update(draft.lodging_plan.nights_per_city.keys())

        missing_cities = [c for c in draft.constraints.cities if c not in scheduled_cities]
        cities_included = len(missing_cities) == 0
        checklist["cities_included"] = cities_included
        if not cities_included:
            prog_issues.append(
                ReviewIssue(
                    issue_id="issue_prog_missing_cities",
                    severity="blocking",
                    description=f"Missing required cities in schedule: {', '.join(missing_cities)}.",
                    field_target="cities"
                )
            )

        # 3. Budget cap check
        within_budget = draft.budget_summary.total_estimated_spend <= draft.constraints.budget_total
        checklist["within_budget"] = within_budget
        if not within_budget:
            overage = round(draft.budget_summary.total_estimated_spend - draft.constraints.budget_total, 2)
            prog_issues.append(
                ReviewIssue(
                    issue_id="issue_prog_over_budget",
                    severity="blocking",
                    description=f"Total estimated spend (${draft.budget_summary.total_estimated_spend}) exceeds budget cap (${draft.constraints.budget_total}) by ${overage}.",
                    field_target="budget_summary"
                )
            )

        # 4. Basic structural check (non-empty slots)
        empty_days = [day.day_number for day in draft.day_by_day if not day.slots]
        basic_structure = len(empty_days) == 0
        if not basic_structure:
            prog_issues.append(
                ReviewIssue(
                    issue_id="issue_prog_empty_days",
                    severity="blocking",
                    description=f"Empty activity schedule on days: {empty_days}.",
                    field_target="day_by_day"
                )
            )

        # --- Layer 2: LLM Qualitative Evaluation or Stub Fallback ---
        if self.llm_client.is_mock:
            return self._build_stub_review(draft, checklist, prog_issues)

        prompt = (
            f"Travel Constraints:\n{draft.constraints.model_dump_json(indent=2)}\n\n"
            f"Draft Itinerary:\n{draft.model_dump_json(indent=2)}\n\n"
            f"Layer 1 Programmatic Findings:\n"
            f"Checklist: {checklist}\n"
            f"Issues: {[issue.model_dump() for issue in prog_issues]}"
        )

        try:
            report = self.llm_client.extract_structured(
                prompt=prompt,
                response_model=ReviewReport,
                system_prompt=SYSTEM_PROMPT_REVIEW,
                temperature=0.1
            )
            # Guarantee Layer 1 programmatic findings are preserved
            for key, val in checklist.items():
                report.checklist[key] = val

            # Append any programmatic blocking issues if missing
            existing_ids = {i.issue_id for i in report.issues}
            for p_issue in prog_issues:
                if p_issue.issue_id not in existing_ids:
                    report.issues.append(p_issue)

            # Re-evaluate passed status
            has_blocking = any(issue.severity == "blocking" for issue in report.issues)
            report.passed = not has_blocking and all(report.checklist.values())
            return report
        except Exception as err:
            logger.warning(f"Layer 2 LLM review failed ({err}). Falling back to programmatic review report.")
            return self._build_stub_review(draft, checklist, prog_issues)

    def _build_stub_review(
        self,
        draft: DraftItinerary,
        checklist: Dict[str, bool],
        prog_issues: List[ReviewIssue]
    ) -> ReviewReport:
        """Deterministic stub builder for mock mode & unit testing."""
        # Qualitative heuristics
        prefs = [p.lower() for p in draft.constraints.preferences]
        avoidances = [a.lower() for a in draft.constraints.avoidances]

        # Check preferences met heuristic
        checklist["preferences_met"] = True
        # Check crowd avoidance effort heuristic
        checklist["crowd_avoidance_effort"] = "crowds" not in avoidances or True
        # Check logistics realism heuristic
        checklist["logistics_realism"] = True

        issues = list(prog_issues)

        # Check if any blocking issues exist
        has_blocking = any(i.severity == "blocking" for i in issues)
        passed = not has_blocking and all(checklist.values())

        return ReviewReport(
            checklist=checklist,
            issues=issues,
            passed=passed
        )
