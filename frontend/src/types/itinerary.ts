export interface TravelConstraints {
  destination_region: string;
  cities: string[];
  duration_days: number;
  budget_total: number;
  currency: string;
  preferences: string[];
  avoidances: string[];
  hard_requirements: string[];
  soft_preferences: string[];
}

export interface DaySlot {
  slot_id: string;
  time_of_day: 'morning' | 'afternoon' | 'evening';
  activity_id?: string;
  activity_name: string;
  travel_time_from_prev_minutes: number;
  notes: string;
}

export interface DaySkeleton {
  day_number: number;
  city: string;
  slots: DaySlot[];
}

export interface LodgingOption {
  id: string;
  city: string;
  neighborhood: string;
  name: string;
  estimated_cost_per_night: number;
  currency: string;
}

export interface LodgingPlan {
  nights_per_city: Record<string, number>;
  suggested_neighborhoods: Record<string, string[]>;
  options: LodgingOption[];
}

export interface MovementPlan {
  inter_city_mode: string;
  transfers: Array<{
    origin?: string;
    destination?: string;
    duration_minutes?: number;
    estimated_cost?: number;
    [key: string]: any;
  }>;
}

export interface BudgetBreakdown {
  per_category_totals: Record<string, number>;
  total_estimated_spend: number;
  within_budget: boolean;
  violations: string[];
  suggested_swaps: Array<Record<string, any>>;
}

export interface ReviewIssue {
  issue_id: string;
  severity: 'blocking' | 'advisory';
  description: string;
  field_target?: string;
}

export interface ReviewReport {
  checklist: Record<string, boolean>;
  issues: ReviewIssue[];
  passed: boolean;
}

export interface FinalItinerary {
  trace_id: string;
  request: string;
  constraints: TravelConstraints;
  day_by_day: DaySkeleton[];
  lodging_plan: LodgingPlan;
  movement_plan: MovementPlan;
  budget_summary: BudgetBreakdown;
  review_report: ReviewReport;
  repair_history: Array<Record<string, any>>;
  narrative_summary: string;
  formatted_markdown?: string;
  disclaimer: string;
}

export interface PlanFinalResponse {
  trace_id: string;
  status: string;
  request: string;
  final_itinerary: FinalItinerary;
  disclaimer: string;
}

export interface PlanApiError {
  message: string;
  status_code?: number;
  trace_id?: string;
}
