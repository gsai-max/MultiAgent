import pytest
import asyncio
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.domain import TravelConstraints, ActivityCatalog, LodgingPlan, MovementPlan, BudgetBreakdown
from backend.app.services.orchestrator import OrchestratorService
from backend.app.services.llm_client import LLMClient

client = TestClient(app)


def test_cors_headers():
    response = client.options(
        "/api/plan",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in ("http://localhost:3000", "*")


@pytest.mark.anyio
async def test_agent_timeout_and_fallback():
    # Instantiate Orchestrator with mock agents where DestinationAgent throws an exception
    orchestrator = OrchestratorService(llm_client=LLMClient(api_key="mock"))
    orchestrator.destination_agent.run = MagicMock(side_effect=RuntimeError("Search API timeout"))

    constraints = TravelConstraints(
        destination_region="Japan",
        cities=["Tokyo"],
        duration_days=3,
        budget_total=1500.0,
        currency="USD"
    )

    # run_parallel_workers should catch the exception gracefully and use fallback catalog
    catalog, (lodging_plan, movement_plan, day_skeletons), budget = await orchestrator.run_parallel_workers(
        constraints, trace_id="trace-fallback-test"
    )

    assert isinstance(catalog, ActivityCatalog)
    assert len(catalog.activities) > 0  # Fallback catalog generated
    assert isinstance(lodging_plan, LodgingPlan)
    assert isinstance(movement_plan, MovementPlan)
    assert isinstance(budget, BudgetBreakdown)


@pytest.mark.anyio
async def test_full_pipeline_hardening_resilience():
    orchestrator = OrchestratorService(llm_client=LLMClient(api_key="mock"))
    request_text = "3 day trip to Tokyo with $1000 budget"

    final_itinerary = await orchestrator.run_full_pipeline(request_text, trace_id="trace-resilience-test")

    assert final_itinerary.trace_id == "trace-resilience-test"
    assert final_itinerary.constraints.duration_days == 3
    assert final_itinerary.review_report is not None
    assert final_itinerary.formatted_markdown is not None
