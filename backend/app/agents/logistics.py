import logging
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.domain import (
    TravelConstraints,
    LodgingPlan,
    LodgingOption,
    MovementPlan,
    DaySkeleton,
    DaySlot
)
from backend.app.services.llm_client import LLMClient
from backend.app.tools.router import ToolRouter

logger = logging.getLogger("ai_travel_planner.agents.logistics")


class LogisticsOutputPayload(BaseModel):
    """Wrapper Pydantic schema for structured output from Logistics LLM extraction."""
    lodging_plan: LodgingPlan
    movement_plan: MovementPlan
    day_skeleton: List[DaySkeleton]


SYSTEM_PROMPT_LOGISTICS = """
You are the Logistics Agent in the AI Travel Planner multi-agent system.
Your job is to determine lodging options, inter-city transport logistics, and daily schedule skeletons.

Instructions:
1. Divide night stays logically across the cities specified in TravelConstraints.
2. Select central, accessible neighborhoods per city.
3. Recommend inter-city transport (e.g., Shinkansen for Tokyo -> Kyoto).
4. Create an ordered sequence of DaySkeleton objects (1 to duration_days) with travel time estimates between activity slots.
5. Use stable IDs for lodging (e.g. lodg_<city>_<index>) and slot IDs (e.g. d<day>_s<slot>).
"""


class LogisticsAgent:
    """Specialist worker agent for accommodation, transit, and daily sequencing (Phase 4b)."""

    def __init__(self, llm_client: Optional[LLMClient] = None, tool_router: Optional[ToolRouter] = None):
        self.llm_client = llm_client or LLMClient()
        self.tool_router = tool_router or ToolRouter()

    def run(
        self,
        constraints: TravelConstraints,
        trace_id: Optional[str] = None
    ) -> Tuple[LodgingPlan, MovementPlan, List[DaySkeleton]]:
        logger.info(f"[TraceID: {trace_id or 'none'}] LogisticsAgent running for duration: {constraints.duration_days} days across {constraints.cities}")

        # Gather geo and lodging price estimates from ToolRouter
        transit_info: List[Dict[str, Any]] = []
        if len(constraints.cities) > 1:
            for i in range(len(constraints.cities) - 1):
                route = self.tool_router.geo_estimate(
                    origin=constraints.cities[i],
                    destination=constraints.cities[i+1],
                    mode="Shinkansen",
                    trace_id=trace_id
                )
                transit_info.append(route)

        lodging_prices: Dict[str, Dict[str, Any]] = {}
        for city in constraints.cities:
            lodging_prices[city] = self.tool_router.price_band(
                category="lodging",
                city=city,
                tier="medium",
                trace_id=trace_id
            )

        if self.llm_client.is_mock:
            return self._build_stub_logistics(constraints, transit_info, lodging_prices)

        prompt = (
            f"Travel Constraints:\n{constraints.model_dump_json(indent=2)}\n\n"
            f"Transit Estimates:\n{transit_info}\n\n"
            f"Lodging Price Bands:\n{lodging_prices}"
        )

        payload = self.llm_client.extract_structured(
            prompt=prompt,
            response_model=LogisticsOutputPayload,
            system_prompt=SYSTEM_PROMPT_LOGISTICS,
            temperature=0.2
        )
        return payload.lodging_plan, payload.movement_plan, payload.day_skeleton

    def _build_stub_logistics(
        self,
        constraints: TravelConstraints,
        transit_info: List[Dict[str, Any]],
        lodging_prices: Dict[str, Dict[str, Any]]
    ) -> Tuple[LodgingPlan, MovementPlan, List[DaySkeleton]]:
        """Deterministic stub logistics builder for mock execution & unit tests."""
        num_cities = len(constraints.cities)
        duration = constraints.duration_days

        # Allocate nights per city
        nights_per_city: Dict[str, int] = {}
        if num_cities == 1:
            nights_per_city[constraints.cities[0]] = duration - 1
        elif num_cities == 2:
            nights_per_city[constraints.cities[0]] = duration // 2
            nights_per_city[constraints.cities[1]] = duration - (duration // 2) - 1
        else:
            base = (duration - 1) // num_cities
            for city in constraints.cities:
                nights_per_city[city] = base
            nights_per_city[constraints.cities[-1]] += (duration - 1) - sum(nights_per_city.values())

        neighborhoods = {
            "Tokyo": ["Asakusa", "Ueno"],
            "Kyoto": ["Gion", "Higashiyama"],
            "Osaka": ["Namba", "Umeda"]
        }

        lodging_options: List[LodgingOption] = []
        suggested_nh: Dict[str, List[str]] = {}

        for city in constraints.cities:
            nh_list = neighborhoods.get(city, ["Central Area"])
            suggested_nh[city] = nh_list
            price_val = lodging_prices.get(city, {}).get("estimated_cost", 140.0)
            lodging_options.append(
                LodgingOption(
                    id=f"lodg_{city.lower()}_01",
                    city=city,
                    neighborhood=nh_list[0],
                    name=f"{city} Central Hotel",
                    estimated_cost_per_night=price_val,
                    currency="USD"
                )
            )

        lodging_plan = LodgingPlan(
            nights_per_city=nights_per_city,
            suggested_neighborhoods=suggested_nh,
            options=lodging_options
        )

        transfers = []
        for info in transit_info:
            transfers.append({
                "from_city": info.get("origin"),
                "to_city": info.get("destination"),
                "mode": info.get("mode", "Shinkansen"),
                "duration_minutes": info.get("duration_minutes", 135),
                "estimated_cost": info.get("estimated_cost_usd", 130.0)
            })

        movement_plan = MovementPlan(
            inter_city_mode="Shinkansen" if transit_info else "Local Transit",
            transfers=transfers
        )

        # Build DaySkeletons
        day_skeletons: List[DaySkeleton] = []
        current_city_idx = 0
        days_in_current_city = 0
        tokyo_nights = nights_per_city.get(constraints.cities[0], 2)

        for day in range(1, duration + 1):
            if day <= tokyo_nights + 1 or num_cities == 1:
                city = constraints.cities[0]
            else:
                city = constraints.cities[1] if num_cities > 1 else constraints.cities[0]

            slots = [
                DaySlot(
                    slot_id=f"d{day}_s1",
                    time_of_day="morning",
                    activity_id=f"act_{city.lower()}_01",
                    activity_name=f"{city} Morning Exploration",
                    travel_time_from_prev_minutes=0,
                    notes=f"Explore highlights in {city}"
                ),
                DaySlot(
                    slot_id=f"d{day}_s2",
                    time_of_day="afternoon",
                    activity_id=f"act_{city.lower()}_02" if num_cities > 1 else f"act_{city.lower()}_01",
                    activity_name=f"{city} Afternoon Stroll & Dining",
                    travel_time_from_prev_minutes=20,
                    notes=f"Relaxed dining and neighborhood walks"
                )
            ]

            day_skeletons.append(
                DaySkeleton(
                    day_number=day,
                    city=city,
                    slots=slots
                )
            )

        return lodging_plan, movement_plan, day_skeletons
