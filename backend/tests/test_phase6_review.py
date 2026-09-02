import pytest
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
    DraftItinerary,
    ReviewReport
)
from backend.app.agents.review import ReviewAgent
from backend.app.services.orchestrator import OrchestratorService
from backend.app.services.llm_client import LLMClient


@pytest.fixture
def valid_constraints():
    return TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=3,
        budget_total=2000.0,
        currency="USD",
        preferences=["food", "temples"],
        avoidances=["crowds"]
    )


@pytest.fixture
def valid_draft(valid_constraints):
    return DraftItinerary(
        constraints=valid_constraints,
        day_by_day=[
            DaySkeleton(
                day_number=1,
                city="Tokyo",
                slots=[
                    DaySlot(slot_id="d1_s1", time_of_day="morning", activity_id="act_tokyo_01", activity_name="Asakusa Temple")
                ]
            ),
            DaySkeleton(
                day_number=2,
                city="Tokyo",
                slots=[
                    DaySlot(slot_id="d2_s1", time_of_day="afternoon", activity_id="act_tokyo_02", activity_name="Meiji Shrine Stroll")
                ]
            ),
            DaySkeleton(
                day_number=3,
                city="Kyoto",
                slots=[
                    DaySlot(slot_id="d3_s1", time_of_day="morning", activity_id="act_kyoto_01", activity_name="Gion Exploration")
                ]
            )
        ],
        lodging_plan=LodgingPlan(
            nights_per_city={"Tokyo": 2, "Kyoto": 1},
            suggested_neighborhoods={"Tokyo": ["Asakusa"], "Kyoto": ["Gion"]},
            options=[
                LodgingOption(id="lodg_1", city="Tokyo", neighborhood="Asakusa", name="Hotel A", estimated_cost_per_night=100.0),
                LodgingOption(id="lodg_2", city="Kyoto", neighborhood="Gion", name="Hotel B", estimated_cost_per_night=120.0)
            ]
        ),
        movement_plan=MovementPlan(inter_city_mode="Shinkansen", transfers=[]),
        budget_summary=BudgetBreakdown(
            per_category_totals={"lodging": 320.0, "transport": 100.0, "food": 150.0, "activities": 50.0},
            total_estimated_spend=620.0,
            within_budget=True
        ),
        narrative_summary="3-day balanced trip to Tokyo and Kyoto."
    )


def test_review_agent_good_draft_passes(valid_draft):
    agent = ReviewAgent(llm_client=LLMClient(api_key="mock"))
    report = agent.run(valid_draft)

    assert isinstance(report, ReviewReport)
    assert report.passed is True
    assert report.checklist["days_match"] is True
    assert report.checklist["cities_included"] is True
    assert report.checklist["within_budget"] is True
    assert report.checklist["preferences_met"] is True
    assert len([i for i in report.issues if i.severity == "blocking"]) == 0


def test_review_agent_fails_on_day_count_mismatch(valid_draft):
    # Alter duration_days to 5 while day_by_day has 3 days
    valid_draft.constraints.duration_days = 5

    agent = ReviewAgent(llm_client=LLMClient(api_key="mock"))
    report = agent.run(valid_draft)

    assert report.passed is False
    assert report.checklist["days_match"] is False
    blocking = [i for i in report.issues if i.severity == "blocking"]
    assert any(i.issue_id == "issue_prog_days_mismatch" for i in blocking)


def test_review_agent_fails_on_missing_city(valid_draft):
    # Require Osaka in constraints, but schedule only has Tokyo and Kyoto
    valid_draft.constraints.cities = ["Tokyo", "Kyoto", "Osaka"]

    agent = ReviewAgent(llm_client=LLMClient(api_key="mock"))
    report = agent.run(valid_draft)

    assert report.passed is False
    assert report.checklist["cities_included"] is False
    blocking = [i for i in report.issues if i.severity == "blocking"]
    assert any(i.issue_id == "issue_prog_missing_cities" for i in blocking)


def test_review_agent_fails_on_over_budget(valid_draft):
    # Increase spend to $3500 when cap is $2000
    valid_draft.budget_summary.total_estimated_spend = 3500.0
    valid_draft.budget_summary.within_budget = False

    agent = ReviewAgent(llm_client=LLMClient(api_key="mock"))
    report = agent.run(valid_draft)

    assert report.passed is False
    assert report.checklist["within_budget"] is False
    blocking = [i for i in report.issues if i.severity == "blocking"]
    assert any(i.issue_id == "issue_prog_over_budget" for i in blocking)


def test_review_agent_fails_on_empty_day_slots(valid_draft):
    # Remove slots from day 2
    valid_draft.day_by_day[1].slots = []

    agent = ReviewAgent(llm_client=LLMClient(api_key="mock"))
    report = agent.run(valid_draft)

    assert report.passed is False
    blocking = [i for i in report.issues if i.severity == "blocking"]
    assert any(i.issue_id == "issue_prog_empty_days" for i in blocking)


def test_orchestrator_review_draft_integration(valid_draft):
    orchestrator = OrchestratorService(llm_client=LLMClient(api_key="mock"))
    report = orchestrator.review_draft(valid_draft, trace_id="review-trace-456")

    assert isinstance(report, ReviewReport)
    assert report.passed is True
