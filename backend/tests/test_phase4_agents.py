"""Phase 4 Test Suite: Specialist Worker Agents (Destination, Logistics, Budget)."""

import pytest
from backend.app.schemas.domain import (
    TravelConstraints,
    ActivityCatalog,
    LodgingPlan,
    MovementPlan,
    DaySkeleton,
    BudgetBreakdown
)
from backend.app.agents.destination import DestinationAgent
from backend.app.agents.logistics import LogisticsAgent
from backend.app.agents.budget import BudgetAgent


@pytest.fixture
def sample_constraints():
    return TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo", "Kyoto"],
        duration_days=5,
        budget_total=3000.0,
        currency="USD",
        preferences=["food", "temples"],
        avoidances=["crowds"],
        hard_requirements=["Fushimi Inari"],
        soft_preferences=[]
    )


def test_destination_agent(sample_constraints):
    agent = DestinationAgent()
    catalog = agent.run(sample_constraints, trace_id="trace-dest-01")

    assert isinstance(catalog, ActivityCatalog)
    assert len(catalog.activities) > 0
    assert "Tokyo" in catalog.notes_by_city or "Kyoto" in catalog.notes_by_city
    assert catalog.activities[0].id.startswith("act_")


def test_logistics_agent(sample_constraints):
    agent = LogisticsAgent()
    lodging, movement, day_skeletons = agent.run(sample_constraints, trace_id="trace-log-01")

    assert isinstance(lodging, LodgingPlan)
    assert isinstance(movement, MovementPlan)
    assert isinstance(day_skeletons, list)
    assert len(day_skeletons) == 5

    assert lodging.options[0].id.startswith("lodg_")
    assert movement.inter_city_mode == "Shinkansen"
    assert day_skeletons[0].slots[0].slot_id.startswith("d1_")


def test_budget_agent_within_budget(sample_constraints):
    logistics_agent = LogisticsAgent()
    dest_agent = DestinationAgent()
    lodging, movement, days = logistics_agent.run(sample_constraints)
    catalog = dest_agent.run(sample_constraints)

    budget_agent = BudgetAgent()
    breakdown = budget_agent.run(sample_constraints, lodging_plan=lodging, catalog=catalog, trace_id="trace-bud-01")

    assert isinstance(breakdown, BudgetBreakdown)
    assert breakdown.within_budget is True
    assert breakdown.total_estimated_spend <= sample_constraints.budget_total
    assert len(breakdown.violations) == 0


def test_budget_agent_over_budget(sample_constraints):
    # Set low budget cap of $500 to trigger over-budget condition
    tight_constraints = sample_constraints.model_copy(update={"budget_total": 500.0})

    logistics_agent = LogisticsAgent()
    dest_agent = DestinationAgent()
    lodging, movement, days = logistics_agent.run(tight_constraints)
    catalog = dest_agent.run(tight_constraints)

    budget_agent = BudgetAgent()
    breakdown = budget_agent.run(tight_constraints, lodging_plan=lodging, catalog=catalog, trace_id="trace-bud-02")

    assert breakdown.within_budget is False
    assert breakdown.total_estimated_spend > 500.0
    assert len(breakdown.violations) > 0
    assert len(breakdown.suggested_swaps) > 0


def test_full_sequential_worker_pass(sample_constraints):
    dest_agent = DestinationAgent()
    logistics_agent = LogisticsAgent()
    budget_agent = BudgetAgent()

    catalog = dest_agent.run(sample_constraints)
    lodging, movement, days = logistics_agent.run(sample_constraints)
    budget = budget_agent.run(sample_constraints, lodging, catalog)

    assert catalog.activities[0].id is not None
    assert lodging.nights_per_city["Tokyo"] > 0
    assert len(movement.transfers) > 0
    assert len(days) == 5
    assert budget.total_estimated_spend > 0
