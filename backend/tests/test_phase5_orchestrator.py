import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.domain import (
    TravelConstraints,
    ActivityCatalog,
    ActivityItem,
    LodgingPlan,
    LodgingOption,
    MovementPlan,
    DaySkeleton,
    DaySlot,
    BudgetBreakdown,
    DraftItinerary
)
from backend.app.services.orchestrator import OrchestratorService
from backend.app.services.llm_client import LLMClient
from backend.app.tools.router import ToolRouter

client = TestClient(app)


@pytest.fixture
def dummy_constraints():
    return TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=3000.0,
        currency="USD",
        preferences=["food", "temples"],
        avoidances=["crowds"],
        hard_requirements=[],
        soft_preferences=[]
    )


@pytest.mark.anyio
async def test_parallel_workers_execution(dummy_constraints):
    llm_client = LLMClient(api_key="mock")
    tool_router = ToolRouter()
    orchestrator = OrchestratorService(llm_client=llm_client, tool_router=tool_router)

    catalog, (lodging_plan, movement_plan, day_skeletons), initial_budget = await orchestrator.run_parallel_workers(
        dummy_constraints, trace_id="test-trace-123"
    )

    assert isinstance(catalog, ActivityCatalog)
    assert len(catalog.activities) > 0
    assert isinstance(lodging_plan, LodgingPlan)
    assert isinstance(movement_plan, MovementPlan)
    assert isinstance(day_skeletons, list)
    assert len(day_skeletons) == 5
    assert isinstance(initial_budget, BudgetBreakdown)


def test_orchestrator_merge_slot_linking(dummy_constraints):
    orchestrator = OrchestratorService(llm_client=LLMClient(api_key="mock"))

    catalog = ActivityCatalog(
        activities=[
            ActivityItem(
                id="act_tokyo_01",
                city="Tokyo",
                name="Sensō-ji Temple Early Visit",
                category="culture",
                estimated_duration_hours=2.0,
                crowd_level="low",
                cost_band="$",
                estimated_cost=15.0,
                must_do=True,
                rationale="Quiet morning temple visit"
            ),
            ActivityItem(
                id="act_kyoto_01",
                city="Kyoto",
                name="Fushimi Inari Taisha Shrine",
                category="culture",
                estimated_duration_hours=3.0,
                crowd_level="low",
                cost_band="$",
                estimated_cost=20.0,
                must_do=True,
                rationale="Historic mountain shrine path"
            )
        ],
        notes_by_city={"Tokyo": "Asakusa area", "Kyoto": "Higashiyama area"}
    )

    lodging_plan = LodgingPlan(
        nights_per_city={"Tokyo": 3, "Kyoto": 1},
        suggested_neighborhoods={"Tokyo": ["Asakusa"], "Kyoto": ["Gion"]},
        options=[
            LodgingOption(
                id="lodg_tokyo_01",
                city="Tokyo",
                neighborhood="Asakusa",
                name="Asakusa Boutique Hotel",
                estimated_cost_per_night=120.0
            )
        ]
    )

    movement_plan = MovementPlan(inter_city_mode="Shinkansen", transfers=[])

    day_skeletons = [
        DaySkeleton(
            day_number=1,
            city="Tokyo",
            slots=[
                DaySlot(
                    slot_id="d1_s1",
                    time_of_day="morning",
                    activity_id="act_tokyo_01",
                    activity_name="Unlinked Activity Name",
                    travel_time_from_prev_minutes=0
                )
            ]
        ),
        DaySkeleton(
            day_number=2,
            city="Kyoto",
            slots=[
                DaySlot(
                    slot_id="d2_s1",
                    time_of_day="morning",
                    activity_id=None,  # Should be linked by merge
                    activity_name="TBD",
                    travel_time_from_prev_minutes=15
                )
            ]
        )
    ]

    initial_budget = BudgetBreakdown(
        per_category_totals={"lodging": 360.0, "transport": 100.0, "food": 250.0, "activities": 35.0},
        total_estimated_spend=745.0,
        within_budget=True
    )

    merged = orchestrator.merge(
        constraints=dummy_constraints,
        catalog=catalog,
        lodging_plan=lodging_plan,
        movement_plan=movement_plan,
        day_skeletons=day_skeletons,
        initial_budget=initial_budget
    )

    assert isinstance(merged, DraftItinerary)
    # Check that slot d1_s1 updated activity_name to match catalog
    assert merged.day_by_day[0].slots[0].activity_name == "Sensō-ji Temple Early Visit"
    # Check that slot d2_s1 was linked to act_kyoto_01
    assert merged.day_by_day[1].slots[0].activity_id == "act_kyoto_01"
    assert merged.day_by_day[1].slots[0].activity_name == "Fushimi Inari Taisha Shrine"


@pytest.mark.anyio
async def test_orchestrator_pipeline_end_to_end(dummy_constraints):
    orchestrator = OrchestratorService(llm_client=LLMClient(api_key="mock"))
    draft = await orchestrator.run_pipeline(dummy_constraints, trace_id="trace-pipeline-test")

    assert isinstance(draft, DraftItinerary)
    assert draft.constraints.duration_days == 5
    assert len(draft.day_by_day) == 5
    assert draft.budget_summary.total_estimated_spend > 0
    assert draft.narrative_summary is not None
    assert "Japan" in draft.narrative_summary or "Tokyo" in draft.narrative_summary



def test_api_plan_endpoint_phase5():
    payload = {
        "request": "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples"
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "trace_id" in data
    assert data["status"] in ("draft_completed", "plan_completed")
    draft = data.get("draft_itinerary") or data.get("final_itinerary")
    assert draft is not None
    assert draft["constraints"]["duration_days"] == 5
    assert len(draft["day_by_day"]) == 5
    assert "budget_summary" in draft
    assert "narrative_summary" in draft

