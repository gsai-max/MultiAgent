import logging
from typing import Optional, List, Dict, Any
from backend.app.schemas.domain import TravelConstraints, ActivityCatalog, ActivityItem
from backend.app.services.llm_client import LLMClient
from backend.app.tools.router import ToolRouter

logger = logging.getLogger("ai_travel_planner.agents.destination")

SYSTEM_PROMPT_DESTINATION = """
You are the Destination Research Agent in the AI Travel Planner multi-agent system.
Your job is to recommend places, temples, culinary experiences, and neighborhood strolls based ONLY on the provided TravelConstraints and Search Results.

Instructions:
1. Recommend experiences for each city in the constraints.
2. Select less-crowded or early morning options when avoidances specify "crowds".
3. Mark high-priority experiences as must_do=true.
4. Return an ActivityCatalog JSON object containing activities (with stable IDs like act_<city>_<index>) and notes_by_city.
"""


class DestinationAgent:
    """Specialist worker agent for destination and experience research (Phase 4a)."""

    def __init__(self, llm_client: Optional[LLMClient] = None, tool_router: Optional[ToolRouter] = None):
        self.llm_client = llm_client or LLMClient()
        self.tool_router = tool_router or ToolRouter()

    def run(self, constraints: TravelConstraints, trace_id: Optional[str] = None) -> ActivityCatalog:
        logger.info(f"[TraceID: {trace_id or 'none'}] DestinationAgent running for region: {constraints.destination_region}, cities: {constraints.cities}")

        # Gather candidate search items via ToolRouter for each city
        search_snippets: List[Dict[str, Any]] = []
        for city in constraints.cities:
            for pref in constraints.preferences or ["sightseeing"]:
                results = self.tool_router.search(query=pref, city=city, trace_id=trace_id)
                search_snippets.extend(results)

        if self.llm_client.is_mock:
            return self._build_stub_catalog(constraints, search_snippets)

        prompt = (
            f"Travel Constraints:\n{constraints.model_dump_json(indent=2)}\n\n"
            f"Search Snippets:\n{search_snippets}"
        )

        catalog = self.llm_client.extract_structured(
            prompt=prompt,
            response_model=ActivityCatalog,
            system_prompt=SYSTEM_PROMPT_DESTINATION,
            temperature=0.2
        )
        return catalog

    def _build_stub_catalog(
        self,
        constraints: TravelConstraints,
        search_snippets: List[Dict[str, Any]]
    ) -> ActivityCatalog:
        """Deterministic stub catalog builder for mock execution & unit tests."""
        activities: List[ActivityItem] = []
        notes: Dict[str, str] = {}

        for idx, item in enumerate(search_snippets, start=1):
            city = item.get("city", constraints.cities[0])
            act_id = f"act_{city.lower()}_{idx:02d}"
            activities.append(
                ActivityItem(
                    id=act_id,
                    city=city,
                    name=item["name"],
                    category=item.get("category", "sightseeing"),
                    estimated_duration_hours=item.get("estimated_duration_hours", 2.0),
                    crowd_level=item.get("crowd_level", "medium"),
                    cost_band=item.get("cost_band", "$$"),
                    estimated_cost=item.get("estimated_cost", 20.0),
                    must_do=item.get("must_do", False),
                    rationale=item.get("rationale", f"Matches preference for {city}")
                )
            )
            if city not in notes:
                notes[city] = f"Curated low-crowd and cultural spots in {city}."

        if not activities:
            # Fallback default activities if search returned empty
            for c_idx, city in enumerate(constraints.cities, start=1):
                act_id = f"act_{city.lower()}_01"
                activities.append(
                    ActivityItem(
                        id=act_id,
                        city=city,
                        name=f"{city} Historic Stroll & Local Dining",
                        category="culture",
                        estimated_duration_hours=3.0,
                        crowd_level="low",
                        cost_band="$$",
                        estimated_cost=30.0,
                        must_do=True,
                        rationale=f"Highlighted experience in {city}"
                    )
                )
                notes[city] = f"Recommended central areas in {city}."

        return ActivityCatalog(activities=activities, notes_by_city=notes)
