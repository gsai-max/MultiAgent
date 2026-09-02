"""Phase 1 Schema Validation & Golden Fixture Tests."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.schemas.domain import (
    TravelConstraints,
    ActivityCatalog,
    LodgingPlan,
    MovementPlan,
    DaySkeleton,
    BudgetBreakdown,
    DraftItinerary,
    ReviewReport,
    RepairHints,
    ActivityItem,
    ReviewIssue
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
GOLDEN_FIXTURE_PATH = FIXTURES_DIR / "japan_5d_golden.json"


@pytest.fixture
def golden_data():
    with open(GOLDEN_FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_parse_golden_fixtures(golden_data):
    """Verify all domain objects parse cleanly from golden fixture without errors."""
    constraints = TravelConstraints.model_validate(golden_data["constraints"])
    assert constraints.destination_region == "Japan"
    assert constraints.duration_days == 5
    assert len(constraints.cities) == 2

    catalog = ActivityCatalog.model_validate(golden_data["activity_catalog"])
    assert len(catalog.activities) == 4
    assert catalog.activities[0].id == "act_tokyo_01"

    lodging = LodgingPlan.model_validate(golden_data["lodging_plan"])
    assert lodging.nights_per_city["Tokyo"] == 2

    movement = MovementPlan.model_validate(golden_data["movement_plan"])
    assert movement.inter_city_mode == "Shinkansen"

    days = [DaySkeleton.model_validate(d) for d in golden_data["day_skeleton"]]
    assert len(days) == 5
    assert days[0].day_number == 1

    budget = BudgetBreakdown.model_validate(golden_data["budget_breakdown"])
    assert budget.within_budget is True

    draft = DraftItinerary.model_validate(golden_data["draft_itinerary"])
    assert draft.constraints.destination_region == "Japan"

    review = ReviewReport.model_validate(golden_data["review_report"])
    assert review.passed is True

    repair = RepairHints.model_validate(golden_data["repair_hints"])
    assert repair.target_agent == "budget"


def test_roundtrip_serialization(golden_data):
    """Verify Pydantic model dump -> load preserves exact data."""
    constraints = TravelConstraints.model_validate(golden_data["constraints"])
    dumped = constraints.model_dump()
    reloaded = TravelConstraints.model_validate(dumped)
    assert constraints == reloaded


def test_invalid_constraints_duration():
    """Verify duration_days < 1 raises ValidationError."""
    with pytest.raises(ValidationError):
        TravelConstraints(
            destination_region="Japan",
            cities=["Tokyo"],
            duration_days=0,
            budget_total=1000.0
        )


def test_invalid_constraints_budget():
    """Verify negative budget_total raises ValidationError."""
    with pytest.raises(ValidationError):
        TravelConstraints(
            destination_region="Japan",
            cities=["Tokyo"],
            duration_days=3,
            budget_total=-100.0
        )


def test_invalid_activity_crowd_level():
    """Verify invalid crowd level enum value raises ValidationError."""
    with pytest.raises(ValidationError):
        ActivityItem(
            id="act_01",
            city="Tokyo",
            name="Test Activity",
            category="sightseeing",
            estimated_duration_hours=1.5,
            crowd_level="super_packed",  # invalid
            cost_band="$",
            estimated_cost=10.0,
            rationale="Test"
        )


def test_invalid_review_issue_severity():
    """Verify invalid severity raises ValidationError."""
    with pytest.raises(ValidationError):
        ReviewIssue(
            issue_id="issue_01",
            severity="fatal",  # invalid, must be blocking or advisory
            description="Fatal error"
        )


def test_cross_reference_activity_ids(golden_data):
    """Verify stable activity IDs referenced in DaySkeleton slots exist in ActivityCatalog."""
    catalog = ActivityCatalog.model_validate(golden_data["activity_catalog"])
    catalog_activity_ids = {act.id for act in catalog.activities}

    days = [DaySkeleton.model_validate(d) for d in golden_data["day_skeleton"]]
    for day in days:
        for slot in day.slots:
            if slot.activity_id:
                assert slot.activity_id in catalog_activity_ids, (
                    f"Day {day.day_number} slot '{slot.slot_id}' references unknown activity ID '{slot.activity_id}'"
                )
