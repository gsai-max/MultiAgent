import logging
from typing import Optional
from backend.app.schemas.domain import FinalItinerary

logger = logging.getLogger("ai_travel_planner.presenter_agent")


class PresenterAgent:
    """
    Presenter Agent (Phase 10 Extension):
    Responsible for generating rich, user-facing presentation snippets (Markdown / HTML)
    from a synthesized FinalItinerary object, keeping UI presentation concerns decoupled
    from core domain logic.
    """

    def format_presentation(self, itinerary: FinalItinerary) -> str:
        """
        Generate a rich, formatted Markdown presentation representation of the FinalItinerary.
        """
        constraints = itinerary.constraints
        days = itinerary.day_by_day
        budget = itinerary.budget_summary
        lodging = itinerary.lodging_plan
        movement = itinerary.movement_plan
        review = itinerary.review_report

        md_lines = []

        # 1. Header Banner & Executive Overview
        md_lines.append(f"# ✈️ Ultimate Trip Itinerary: {constraints.destination_region}")
        md_lines.append(
            f"> **Duration:** {constraints.duration_days} Days | "
            f"**Cities:** {', '.join(constraints.cities)} | "
            f"**Est. Budget:** ${budget.total_estimated_spend} / ${constraints.budget_total} {constraints.currency}\n"
        )

        md_lines.append("## 🌟 Executive Overview")
        md_lines.append(f"{itinerary.narrative_summary}\n")

        # 2. Human In The Loop Advisory if applicable
        if itinerary.requires_human_review:
            md_lines.append(
                "> ⚠️ **HUMAN REVIEW RECOMMENDED:** This itinerary contains advisory flags or "
                "logistics balance notes requiring manual review before booking.\n"
            )

        # 3. Day by Day Schedule
        md_lines.append("## 📅 Day-by-Day Detailed Schedule\n")
        for day in days:
            md_lines.append(f"### Day {day.day_number}: {day.city}")
            for slot in day.slots:
                transit_str = f" _({slot.travel_time_from_prev_minutes}m transit)_" if slot.travel_time_from_prev_minutes > 0 else ""
                md_lines.append(f"- **{slot.time_of_day.upper()}**: {slot.activity_name}{transit_str}")
                if slot.notes:
                  md_lines.append(f"  - *Note:* {slot.notes}")
            md_lines.append("")

        # 4. Lodging & Inter-City Transit
        md_lines.append("## 🏨 Accommodation & Inter-City Transit")
        md_lines.append(f"- **Primary Transit Mode:** {movement.inter_city_mode}")
        if lodging.options:
            md_lines.append("- **Suggested Lodging Options:**")
            for opt in lodging.options:
                md_lines.append(
                    f"  - **{opt.name}** ({opt.city} — {opt.neighborhood}): "
                    f"~${opt.estimated_cost_per_night}/night"
                )
        md_lines.append("")

        # 5. Budget Allocation
        md_lines.append("## 💰 Budget & Cost Breakdown")
        for cat, val in budget.per_category_totals.items():
            md_lines.append(f"- **{cat.capitalize()}:** ${val} {constraints.currency}")
        md_lines.append(f"- **Total Estimated Spend:** ${budget.total_estimated_spend} {constraints.currency}")
        if not budget.within_budget:
            md_lines.append("  - ⚠️ *Note: Total spend exceeds original target budget cap.*")
        md_lines.append("")

        # 6. Quality Gate Verification
        md_lines.append("## 🛡️ Quality Gate Verification Report")
        status_symbol = "✅ Passed" if review.passed else "⚠️ Flagged for Advisory Review"
        md_lines.append(f"- **Overall Quality Gate Status:** {status_symbol}")
        passed_rules = [k for k, v in review.checklist.items() if v]
        md_lines.append(f"- **Verified Rules ({len(passed_rules)}/{len(review.checklist)}):** {', '.join(passed_rules)}")
        md_lines.append("")

        # 7. Disclaimer
        md_lines.append("---")
        md_lines.append(f"**Disclaimer:** {itinerary.disclaimer}")

        return "\n".join(md_lines)
