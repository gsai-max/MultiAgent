# ✈️ AI Travel Planner — Multi-Agent Travel Engine

An intelligent full-stack travel planning application built with Python (FastAPI), React (TypeScript + Vite), and Pydantic. It transforms natural language travel requests into comprehensive, validated, day-by-day itineraries with lodging suggestions, transit logistics, category budget breakdowns, quality gate reviews, and an interactive web UI.

---

## 🏛️ System Architecture

The application combines a multi-agent backend with a modern React web frontend:

```
                  ┌───────────────────────────────┐
                  │    React + Vite Web UI        │
                  │   (Request Form & Dashboard)  │
                  └───────────────┬───────────────┘
                                  │ POST /api/plan
                                  ▼
               ┌─────────────────────────────────────┐
               │    Constraint Extractor (Part A)    │
               └──────────────────┬──────────────────┘
                                  │ (TravelConstraints)
                                  ▼
      ┌───────────────────────────┼───────────────────────────┐
      │ Parallel Execution        │                           │
      ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│ Destination  │          │  Logistics   │            │    Budget    │
│    Agent     │          │    Agent     │            │    Agent     │
└──────┬───────┘          └──────┬───────┘            └──────┬───────┘
       │ ActivityCatalog         │ Lodging+Movement          │ BudgetBreakdown
       └─────────────────────────┼───────────────────────────┘
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │    Orchestrator Merge (Part B)      │
               └──────────────────┬──────────────────┘
                                  │ (DraftItinerary)
                                  ▼
               ┌─────────────────────────────────────┐
               │       Review Agent Gate (Phase 6)   │
               └──────────────────┬──────────────────┘
                                  │
                          Pass / Fail Gate
                                  │
               ┌──────────────────┴──────────────────┐
               │  Bounded Repair Loop (Phase 7)      │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │   FinalItinerary + Web UI Rendering │
               └─────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Backend Setup & Run

```powershell
# Navigate to repository root
cd "MultiAgent"

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # macOS / Linux

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
# Copy .env.example to .env
# Set LLM_API_KEY (or use 'mock' for offline testing)

# Run FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`.

### 2. Frontend Setup & Run (Phase 9)

```powershell
# In a new terminal window:
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend Web App will be running at `http://localhost:5173`.

---

## 📡 API Reference

### Health Check
**GET** `/health`

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "ai-travel-planner-backend"
}
```

---

### Generate Trip Plan
**POST** `/api/plan`

**Headers:** `Content-Type: application/json`

**Sample Request:**
```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "request": "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples"
  }'
```

**Sample Response:**
```json
{
  "trace_id": "trace-63e818d788d6",
  "status": "plan_completed",
  "request": "5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples",
  "final_itinerary": {
    "constraints": {
      "destination_region": "Japan",
      "cities": ["Tokyo", "Kyoto"],
      "duration_days": 5,
      "budget_total": 3000.0,
      "currency": "USD",
      "preferences": ["food", "temples"],
      "avoidances": ["crowds"]
    },
    "day_by_day": [
      {
        "day_number": 1,
        "city": "Tokyo",
        "slots": [
          {
            "slot_id": "d1_s1",
            "time_of_day": "morning",
            "activity_id": "act_tokyo_01",
            "activity_name": "Tokyo Morning Exploration",
            "travel_time_from_prev_minutes": 0
          }
        ]
      }
    ],
    "budget_summary": {
      "per_category_totals": {
        "lodging": 560.0,
        "transport": 335.0,
        "food": 250.0,
        "activities": 60.0
      },
      "total_estimated_spend": 1205.0,
      "within_budget": true
    },
    "formatted_markdown": "# ✈️ 5-Day Trip Itinerary: Japan\n...",
    "disclaimer": "This itinerary is an illustrative demonstration generated by AI Travel Planner multi-agent system. Logistics, pricing, and bookings are not guaranteed real-time inventory."
  },
  "disclaimer": "This itinerary is an illustrative demonstration generated by AI Travel Planner multi-agent system..."
}
```

---

## 📚 Documentation & Deployment

For detailed architectural specs and production deployment guides, refer to:
- 📖 [**Architecture Spec**](file:///c:/Nextleap%20Projects%20Git/MultiAgent/docs/Architecture.md)
- 📋 [**Implementation Plan**](file:///c:/Nextleap%20Projects%20Git/MultiAgent/docs/ImplementationPlan.md)
- 🛡️ [**Edge Case Guide**](file:///c:/Nextleap%20Projects%20Git/MultiAgent/docs/EdgeCase.md)
- 🚀 [**Deployment Plan**](file:///c:/Nextleap%20Projects%20Git/MultiAgent/docs/DeploymentPlan.md) *(Backend on Render + Frontend on Vercel)*
- 🛠️ [**Render Blueprint Config**](file:///c:/Nextleap%20Projects%20Git/MultiAgent/render.yaml)

---

## 🧪 Running Automated Tests & Production Build

### Backend Tests
Run the complete Python test suite across all phases:

```powershell
$env:PYTHONPATH="."; .venv\Scripts\python -m pytest
```

Test coverage includes:
- **Phase 0:** API skeleton & trace ID middleware
- **Phase 1:** Domain models & JSON Schema validation
- **Phase 2:** Constraint Extractor & structured output
- **Phase 3:** ToolRouter stubs & caching
- **Phase 4:** Specialist agents (Destination, Logistics, Budget)
- **Phase 5:** Orchestrator merge & parallel execution
- **Phase 6:** Review Agent programmatic & LLM quality gate
- **Phase 7:** Bounded repair loop & `FinalItinerary` synthesis
- **Phase 8:** CORS middleware, agent timeouts & fallback resilience

### Frontend Build
Compile TypeScript and bundle web assets for production:

```powershell
cd frontend
npm run build
```
Outputs static bundle to `frontend/dist/`.
