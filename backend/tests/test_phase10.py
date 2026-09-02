import pytest
import os
import shutil
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.domain import (
    FinalItinerary, TravelConstraints, DaySkeleton, DaySlot,
    LodgingPlan, LodgingOption, MovementPlan, BudgetBreakdown, ReviewReport
)
from backend.app.services.plan_store import PlanStateStore
from backend.app.agents.presenter_agent import PresenterAgent
from backend.app.tools.router import ToolRouter

client = TestClient(app)

TEST_STORAGE_DIR = "backend/tests/tmp_plan_store"


@pytest.fixture(autouse=True)
def cleanup_tmp_store():
    yield
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


def build_sample_final_itinerary(trace_id="trace-test-101", requires_human_review=False) -> FinalItinerary:
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=3000.0,
        currency="USD"
    )
    day1 = DaySkeleton(
        day_number=1,
        city="Tokyo",
        slots=[
            DaySlot(slot_id="s1", time_of_day="morning", activity_name="Shibuya Crossing Walk")
        ]
    )
    lodging = LodgingPlan(
        nights_per_city={"Tokyo": 2, "Kyoto": 2},
        suggested_neighborhoods={"Tokyo": ["Shibuya"], "Kyoto": ["Gion"]},
        options=[
            LodgingOption(id="l1", city="Tokyo", neighborhood="Shibuya", name="Shibuya Hotel", estimated_cost_per_night=120.0)
        ]
    )
    movement = MovementPlan(inter_city_mode="Shinkansen", transfers=[])
    budget = BudgetBreakdown(
        per_category_totals={"lodging": 480.0, "transport": 200.0, "food": 250.0, "activities": 100.0},
        total_estimated_spend=1030.0,
        within_budget=True
    )
    review = ReviewReport(
        checklist={"days_match": True, "within_budget": True},
        issues=[],
        passed=not requires_human_review
    )
    return FinalItinerary(
        trace_id=trace_id,
        request="5 day trip to Tokyo and Kyoto with $3000 budget",
        constraints=constraints,
        day_by_day=[day1],
        lodging_plan=lodging,
        movement_plan=movement,
        budget_summary=budget,
        review_report=review,
        narrative_summary="Sample 5-day Japan trip narrative.",
        requires_human_review=requires_human_review
    )


def test_plan_state_store_save_and_retrieve():
    store = PlanStateStore(storage_dir=TEST_STORAGE_DIR)
    itinerary = build_sample_final_itinerary(trace_id="trace-store-001")

    store.save_plan(itinerary)

    retrieved = store.get_plan("trace-store-001")
    assert retrieved is not None
    assert retrieved.trace_id == "trace-store-001"
    assert retrieved.constraints.destination_region == "Japan"

    summaries = store.list_plans()
    assert len(summaries) == 1
    assert summaries[0]["trace_id"] == "trace-store-001"


def test_presenter_agent_formatting():
    presenter = PresenterAgent()
    itinerary = build_sample_final_itinerary(trace_id="trace-presenter-001")

    presentation = presenter.format_presentation(itinerary)
    assert "Ultimate Trip Itinerary: Japan" in presentation
    assert "Shibuya Crossing Walk" in presentation
    assert "Shinkansen" in presentation
    assert "Disclaimer:" in presentation


def test_tool_router_rag_guides():
    router = ToolRouter()
    guide = router.get_travel_guide("Japan", "Tokyo")
    assert guide is not None
    assert "Shibuya" in guide["neighborhoods"]
    assert "Sensō-ji Temple" in guide["must_do"]


def test_api_get_plan_by_id_and_plans_history():
    store = PlanStateStore(storage_dir=TEST_STORAGE_DIR)
    itinerary = build_sample_final_itinerary(trace_id="trace-api-999")
    store.save_plan(itinerary)

    # Wire to global orchestrator for test client
    from backend.app.routers.plan import orchestrator
    orchestrator.plan_store.save_plan(itinerary)

    response_list = client.get("/api/plans")
    assert response_list.status_code == 200
    plans_data = response_list.json()["plans"]
    assert any(p["trace_id"] == "trace-api-999" for p in plans_data)

    response_get = client.get("/api/plan/trace-api-999")
    assert response_get.status_code == 200
    plan_json = response_get.json()
    assert plan_json["trace_id"] == "trace-api-999"
    assert plan_json["final_itinerary"]["constraints"]["destination_region"] == "Japan"


def test_api_get_plan_404_not_found():
    response = client.get("/api/plan/nonexistent-trace-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
