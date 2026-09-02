"""Domain Schemas for AI Travel Planner Multi-Agent System."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class TravelConstraints(BaseModel):
    """Extracted travel constraints produced by Orchestrator for all specialist agents."""
    destination_region: str = Field(..., description="Target country or geographic region")
    cities: List[str] = Field(..., min_length=1, description="List of primary target cities")
    duration_days: int = Field(..., ge=1, description="Total trip duration in days")
    budget_total: float = Field(..., ge=0, description="Maximum overall budget cap")
    currency: str = Field(default="USD", description="Currency symbol/code for all cost fields")
    preferences: List[str] = Field(default_factory=list, description="User interest tags (e.g. food, temples)")
    avoidances: List[str] = Field(default_factory=list, description="User dislikes/avoidances (e.g. crowds)")
    hard_requirements: List[str] = Field(default_factory=list, description="Non-negotiable requirements")
    soft_preferences: List[str] = Field(default_factory=list, description="Nice-to-have preferences")


class ActivityItem(BaseModel):
    """Single catalog activity produced by Destination Research Agent."""
    id: str = Field(..., description="Stable unique activity ID (e.g., act_tokyo_shibuya_01)")
    city: str = Field(..., description="City where activity takes place")
    name: str = Field(..., description="Activity name")
    category: str = Field(..., description="Category tag (temple, food, museum, nature, etc.)")
    estimated_duration_hours: float = Field(..., gt=0, description="Estimated duration in hours")
    crowd_level: Literal["low", "medium", "high"] = Field(..., description="Crowd rating")
    cost_band: Literal["$", "$$", "$$$"] = Field(..., description="Relative cost band")
    estimated_cost: float = Field(..., ge=0, description="Estimated cost per person")
    must_do: bool = Field(default=False, description="Flag indicating if activity is a high-priority must-do")
    rationale: str = Field(..., description="Why this activity matches preferences")


class ActivityCatalog(BaseModel):
    """Catalog of research experiences produced by Destination Agent."""
    activities: List[ActivityItem] = Field(..., description="List of suggested catalog activities")
    notes_by_city: Dict[str, str] = Field(default_factory=dict, description="Neighborhood & atmosphere notes per city")


class LodgingOption(BaseModel):
    """Single lodging suggestion option produced by Logistics Agent."""
    id: str = Field(..., description="Stable unique lodging ID (e.g., lodg_tokyo_shinjuku_01)")
    city: str = Field(..., description="Target city")
    neighborhood: str = Field(..., description="Suggested neighborhood or area")
    name: str = Field(..., description="Hotel/Ryokan or area stay option name")
    estimated_cost_per_night: float = Field(..., ge=0, description="Estimated cost per night")
    currency: str = Field(default="USD", description="Currency")


class LodgingPlan(BaseModel):
    """Lodging breakdown produced by Logistics Agent."""
    nights_per_city: Dict[str, int] = Field(..., description="Number of nights staying per city")
    suggested_neighborhoods: Dict[str, List[str]] = Field(..., description="Recommended stay areas per city")
    options: List[LodgingOption] = Field(..., description="List of specific lodging options with stable IDs")


class MovementPlan(BaseModel):
    """Inter-city transportation plan produced by Logistics Agent."""
    inter_city_mode: str = Field(..., description="Primary transit mode (e.g., Shinkansen, Express Train)")
    transfers: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of transfers containing origin, destination, duration_minutes, estimated_cost"
    )


class DaySlot(BaseModel):
    """Single ordered activity slot within a day skeleton."""
    slot_id: str = Field(..., description="Unique slot identifier within the day")
    time_of_day: Literal["morning", "afternoon", "evening"] = Field(..., description="Time window")
    activity_id: Optional[str] = Field(None, description="Linked stable ID from ActivityCatalog")
    activity_name: str = Field(..., description="Name of scheduled activity or rest block")
    travel_time_from_prev_minutes: int = Field(default=0, ge=0, description="Estimated transit time from prior slot")
    notes: str = Field(default="", description="Pacing or movement notes")


class DaySkeleton(BaseModel):
    """Single day schedule skeleton produced by Logistics Agent."""
    day_number: int = Field(..., ge=1, description="Day index (1-based)")
    city: str = Field(..., description="City for the day")
    slots: List[DaySlot] = Field(..., description="Ordered activity slots for the day")


class BudgetBreakdown(BaseModel):
    """Budget calculation produced by Budget Agent."""
    per_category_totals: Dict[str, float] = Field(
        ...,
        description="Cost breakdown mapping (lodging, transport, food, activities)"
    )
    total_estimated_spend: float = Field(..., ge=0, description="Sum total of all estimated spend")
    within_budget: bool = Field(..., description="Flag indicating if total spend <= constraints budget_total")
    violations: List[str] = Field(default_factory=list, description="List of budget violation messages")
    suggested_swaps: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested cost-saving item swaps")


class DraftItinerary(BaseModel):
    """Merged itinerary draft created by Orchestrator combining specialist outputs."""
    constraints: TravelConstraints = Field(..., description="Original travel constraints")
    day_by_day: List[DaySkeleton] = Field(..., description="Full day-by-day outline")
    lodging_plan: LodgingPlan = Field(..., description="Lodging plan")
    movement_plan: MovementPlan = Field(..., description="Inter-city movement plan")
    budget_summary: BudgetBreakdown = Field(..., description="Combined budget breakdown")
    narrative_summary: Optional[str] = Field(None, description="Merged narrative overview of the trip")


class ReviewIssue(BaseModel):
    """Single issue flag raised by Review Agent."""
    issue_id: str = Field(..., description="Stable unique issue ID (e.g. issue_budget_01)")
    severity: Literal["blocking", "advisory"] = Field(..., description="Issue severity")
    description: str = Field(..., description="Detailed description of the rule violation or quality issue")
    field_target: Optional[str] = Field(None, description="Target field/component associated with issue")


class ReviewReport(BaseModel):
    """Quality gate verification report produced by Review Agent."""
    checklist: Dict[str, bool] = Field(
        ...,
        description="Checklist map (days_match, cities_included, within_budget, preferences_met, crowd_avoidance_effort, logistics_realism)"
    )
    issues: List[ReviewIssue] = Field(default_factory=list, description="List of identified issues")
    passed: bool = Field(..., description="Overall review gate pass/fail decision")


class RepairHints(BaseModel):
    """Actionable repair suggestions returned to Orchestrator when Review fails."""
    target_agent: Literal["destination", "logistics", "budget", "orchestrator"] = Field(
        ..., description="Agent designated to perform repair"
    )
    suggestions: List[str] = Field(..., description="Human-readable repair instructions")
    action_type: Literal["trim_cost", "rebalance_days", "swap_activity", "adjust_lodging"] = Field(
        ..., description="Categorized repair strategy"
    )


class FinalItinerary(BaseModel):
    """Final user-facing itinerary produced after Review gate & repair loop (Phase 7)."""
    trace_id: str = Field(..., description="Unique request trace ID")
    request: str = Field(..., description="Original user request string")
    constraints: TravelConstraints = Field(..., description="Extracted travel constraints")
    day_by_day: List[DaySkeleton] = Field(..., description="Final day-by-day outline")
    lodging_plan: LodgingPlan = Field(..., description="Final lodging plan")
    movement_plan: MovementPlan = Field(..., description="Final inter-city movement plan")
    budget_summary: BudgetBreakdown = Field(..., description="Final budget summary")
    review_report: ReviewReport = Field(..., description="Final ReviewReport quality gate output")
    repair_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of repair attempts made")
    narrative_summary: str = Field(..., description="Comprehensive overview narrative")
    formatted_markdown: Optional[str] = Field(None, description="Formatted Markdown representation for presentation/UI")
    presenter_output: Optional[str] = Field(None, description="Presenter Agent rich presentation HTML/Markdown snippet")
    requires_human_review: bool = Field(default=False, description="Flag indicating if plan failed review quality gate after max repairs and needs human review")
    disclaimer: str = Field(
        default=(
            "This itinerary is an illustrative demonstration generated by AI Travel Planner multi-agent system. "
            "Logistics, pricing, and bookings are not guaranteed real-time inventory."
        ),
        description="Disclaimer note"
    )


