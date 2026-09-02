"""Phase 0 Integration Tests."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-travel-planner-backend"
    assert "X-Trace-ID" in response.headers

def test_create_plan_stub():
    payload = {"request": "5 day trip to Tokyo and Kyoto with $3000 budget"}
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "trace_id" in data
    assert data["trace_id"].startswith("trace-")
    assert data["request"] == payload["request"]
    assert data["status"] in ("stub_completed", "draft_completed", "plan_completed")
    assert "final_itinerary" in data or "draft_itinerary" in data or "constraints_summary" in data
    assert "disclaimer" in data
    assert response.headers.get("X-Trace-ID") == data["trace_id"]

def test_create_plan_empty_request():
    payload = {"request": "   "}
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Request text cannot be empty."
