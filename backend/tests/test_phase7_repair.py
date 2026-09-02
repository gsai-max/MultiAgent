import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.domain import (
    TravelConstraints,
    DraftItinerary,
    LodgingPlan,
    LodgingOption,
    MovementPlan,
    DaySkeleton,
    DaySlot,
    BudgetBreakdown,
    FinalItinerary
)
from backend.app.services.orchestrator import OrchestratorService
from backend.app.agents.review import ReviewAgent
from backend.app.services.llm_client import LLMClient

client = TestClient(app)


@pytest.fixture
def mock_orchestrator():
    return OrchestratorService(llm_client=LLMClient(api_key="mock"))


@pytest.fixture
def sample_overbudget_draft():
    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=3,
        budget_total=400.0,  # Tight budget cap of $400
        currency="USD",
        preferences=["food"],
        avoidances=[]
    )
    return DraftItinerary(
        constraints=constraints,
        day_by_day=[
            DaySkeleton(
                day_number=1,
                city="Tokyo",
                slots=[DaySlot(slot_id="d1_s1", time_of_day="morning", activity_id="act_1", activity_name="Tour")]
            ),
            DaySkeleton(
                day_number=2,
                city="Tokyo",
                slots=[DaySlot(slot_id="d2_s1", time_of_day="afternoon", activity_id="act_2", activity_name="Dining")]
            ),
            DaySkeleton(
                day_number=3,
                city="Kyoto",
                slots=[DaySlot(slot_id="d3_s1", time_of_day="morning", activity_id="act_3", activity_name="Shrine")]
            )
        ],
        lodging_plan=LodgingPlan(
            nights_per_city={"Tokyo": 2, "Kyoto": 1},
            suggested_neighborhoods={"Tokyo": ["Shinjuku"], "Kyoto": ["Gion"]},
            options=[
                LodgingOption(id="l1", city="Tokyo", neighborhood="Shinjuku", name="Luxury Hotel Tokyo", estimated_cost_per_night=300.0),
                LodgingOption(id="l2", city="Kyoto", neighborhood="Gion", name="Luxury Hotel Kyoto", estimated_cost_per_night=250.0)
            ]
        ),
        movement_plan=MovementPlan(inter_city_mode="Shinkansen", transfers=[]),
        budget_summary=BudgetBreakdown(
            per_category_totals={"lodging": 850.0, "transport": 100.0, "food": 150.0, "activities": 50.0},
            total_estimated_spend=1150.0,
            within_budget=False,
            violations=["Over budget by $750"]
        ),
        narrative_summary="3-day high-budget trip."
    )


def test_apply_repairs_over_budget(mock_orchestrator, sample_overbudget_draft):
    review_report = mock_orchestrator.review_draft(sample_overbudget_draft)
    assert review_report.passed is False

    repaired_draft, record = mock_orchestrator.apply_repairs(sample_overbudget_draft, review_report)

    # Lodging cost per night should be capped at budget level ($80/night)
    for opt in repaired_draft.lodging_plan.options:
        assert opt.estimated_cost_per_night <= 80.0

    assert len(record["actions_taken"]) > 0


def test_apply_repairs_day_mismatch(mock_orchestrator, sample_overbudget_draft):
    # Set duration_days to 5, but day_by_day has 3 days
    sample_overbudget_draft.constraints.duration_days = 5
    review_report = mock_orchestrator.review_draft(sample_overbudget_draft)

    repaired_draft, record = mock_orchestrator.apply_repairs(sample_overbudget_draft, review_report)
    assert len(repaired_draft.day_by_day) == 5


def test_generate_presentation_markdown(mock_orchestrator, sample_overbudget_draft):
    review_report = mock_orchestrator.review_draft(sample_overbudget_draft)
    markdown = mock_orchestrator.generate_presentation_markdown(sample_overbudget_draft, review_report)

    assert "# ✈️ 3-Day Trip Itinerary: Japan" in markdown
    assert "## 📅 Day-by-Day Schedule" in markdown
    assert "## 💰 Budget Breakdown" in markdown
    assert "## 🛡️ Quality Review Status" in markdown


@pytest.mark.anyio
async def test_run_full_pipeline(mock_orchestrator):
    request_text = "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples"
    final_plan = await mock_orchestrator.run_full_pipeline(request_text, trace_id="trace-p7-test")

    assert isinstance(final_plan, FinalItinerary)
    assert final_plan.trace_id == "trace-p7-test"
    assert final_plan.constraints.duration_days == 5
    assert len(final_plan.day_by_day) == 5
    assert final_plan.formatted_markdown is not None
    assert "Trip Itinerary" in final_plan.formatted_markdown


def test_api_plan_endpoint_phase7():
    payload = {
        "request": "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples"
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "trace_id" in data
    assert data["status"] == "plan_completed"
    assert "final_itinerary" in data
    fit = data["final_itinerary"]
    assert fit["constraints"]["duration_days"] == 5
    assert len(fit["day_by_day"]) == 5
    assert "formatted_markdown" in fit
    assert fit["disclaimer"] is not None
