import json
import logging
import os
from typing import Dict, List, Any, Optional
from backend.app.schemas.domain import FinalItinerary

logger = logging.getLogger("ai_travel_planner.plan_store")


class PlanStateStore:
    """
    Durable PlanState Store (Phase 10 Extension):
    Manages persistence, retrieval, and audit history of FinalItinerary objects.
    Supports in-memory caching and optional file-system persistence in `backend/data/plans/`.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            # Default to backend/data/plans
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            storage_dir = os.path.join(base_dir, "data", "plans")
        
        self.storage_dir = storage_dir
        self._memory_cache: Dict[str, FinalItinerary] = {}
        self._ensure_storage_dir()
        self._load_persisted_plans()

    def _ensure_storage_dir(self):
        """Create storage directory if it does not exist."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create storage directory '{self.storage_dir}': {e}")

    def _load_persisted_plans(self):
        """Load persisted plan JSON files from disk into memory cache."""
        if not os.path.exists(self.storage_dir):
            return

        try:
            for fname in os.listdir(self.storage_dir):
                if fname.endswith(".json"):
                    filepath = os.path.join(self.storage_dir, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        itinerary = FinalItinerary.model_validate(data)
                        self._memory_cache[itinerary.trace_id] = itinerary
            logger.info(f"Loaded {len(self._memory_cache)} saved plans from '{self.storage_dir}'.")
        except Exception as e:
            logger.warning(f"Error loading persisted plans: {e}")

    def save_plan(self, itinerary: FinalItinerary) -> None:
        """Save a FinalItinerary to memory cache and disk persistence."""
        self._memory_cache[itinerary.trace_id] = itinerary

        if os.path.exists(self.storage_dir):
            filepath = os.path.join(self.storage_dir, f"{itinerary.trace_id}.json")
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(itinerary.model_dump(), f, indent=2)
                logger.info(f"Persisted plan '{itinerary.trace_id}' to {filepath}")
            except Exception as e:
                logger.error(f"Failed to persist plan '{itinerary.trace_id}' to disk: {e}")

    def get_plan(self, trace_id: str) -> Optional[FinalItinerary]:
        """Fetch a saved plan by trace ID."""
        return self._memory_cache.get(trace_id)

    def list_plans(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List summary info for stored plans in reverse chronological order."""
        plans = list(self._memory_cache.values())
        # Return recent plans first
        plans_sorted = sorted(plans, key=lambda p: p.trace_id, reverse=True)[:limit]
        
        summaries = []
        for p in plans_sorted:
            summaries.append({
                "trace_id": p.trace_id,
                "request": p.request,
                "destination_region": p.constraints.destination_region,
                "duration_days": p.constraints.duration_days,
                "cities": p.constraints.cities,
                "total_spend": p.budget_summary.total_estimated_spend,
                "currency": p.constraints.currency,
                "passed_review": p.review_report.passed,
                "requires_human_review": p.requires_human_review,
            })
        return summaries
