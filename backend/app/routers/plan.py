import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Union, List, Dict, Any
from backend.app.schemas.plan import PlanRequest, PlanStubResponse, PlanDraftResponse, PlanFinalResponse
from backend.app.services.orchestrator import OrchestratorService

logger = logging.getLogger("ai_travel_planner.plan")
router = APIRouter(prefix="/api", tags=["Plan"])
orchestrator = OrchestratorService()

@router.post("/plan", response_model=Union[PlanFinalResponse, PlanDraftResponse, PlanStubResponse])
async def create_plan(plan_req: PlanRequest, request: Request):
    if not plan_req.request.strip():
        raise HTTPException(status_code=400, detail="Request text cannot be empty.")
    
    trace_id = getattr(request.state, "trace_id", "unknown-trace")
    logger.info(f"[TraceID: {trace_id}] Received plan request: '{plan_req.request[:50]}...'")

    # Run Orchestrator full pipeline (Extraction -> Parallel Workers -> Merge -> Review Gate -> Bounded Repair -> FinalItinerary)
    final_itinerary = await orchestrator.run_full_pipeline(plan_req.request, trace_id=trace_id)

    response = PlanFinalResponse(
        trace_id=trace_id,
        request=plan_req.request,
        final_itinerary=final_itinerary.model_dump()
    )
    return response


@router.get("/plans")
async def list_plans():
    """List history of generated travel plans."""
    summaries = orchestrator.plan_store.list_plans()
    return {"plans": summaries}


@router.get("/plan/{trace_id}")
async def get_plan_by_id(trace_id: str):
    """Retrieve a saved travel plan by its unique trace ID."""
    itinerary = orchestrator.plan_store.get_plan(trace_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail=f"Plan with trace ID '{trace_id}' not found.")
    
    return PlanFinalResponse(
        trace_id=trace_id,
        request=itinerary.request,
        final_itinerary=itinerary.model_dump()
    )
