# Architecture: AI Travel Planner — System Architecture

> **Project:** Automations & Multi-Agent Systems — Graduation Project
> **Related:** [`context.md`](./context.md) | [`ProblemStatement.txt`](../ProblemStatement.txt)

---

## Overview

The system turns a natural-language travel request into a structured trip plan by coordinating specialized agents. Success is measured by **constraint satisfaction** (duration, cities, budget, preferences) and **plausibility** (logistics, pacing), not by booking real inventory.

The product is delivered as a **full-stack application**: a backend service that runs the multi-agent pipeline and exposes a stable HTTP API, and a frontend that collects the user request and presents the final itinerary (and intermediate status when desired).

---

## Application Architecture: Backend and Frontend

### Backend

The backend is the **only** component that holds API keys, calls the LLM, runs agents, and invokes the tool router.

**Responsibilities:**

| Concern | Detail |
|---|---|
| **HTTP API** | Validate inbound requests (body size, required fields), attach trace ID, return JSON (and optional streamed tokens if streaming is added later) |
| **Orchestration runtime** | Implements the agent pipeline: constraint extraction, parallel workers, merge, Review, repair loop |
| **Configuration and secrets** | Model names, timeouts, tool endpoints; never expose secrets to the browser |
| **Cross-origin and transport** | CORS policy restricted to frontend origin(s); HTTPS in deployed environments |
| **Operational concerns** | Rate limiting or simple auth for public demos, request timeouts, structured error responses (validation vs upstream LLM vs timeout) |

**Suggested API Surface:**

| Operation | Purpose |
|---|---|
| `GET /health` | Liveness for load balancers and frontend preflight |
| `POST /api/plan` | Body: natural-language request string (+ optional flags). Response: `FinalItinerary` payload (structured fields + markdown/HTML snippet), extracted `TravelConstraints` summary, review summary, and `trace_id` |
| `GET /api/plan/{id}` *(optional)* | If plans are persisted: fetch a prior result by ID |

> **Long-running plans:** Prefer a single request with server-side timeout for educational scope; optional SSE or job ID + polling if UX requires partial progress without changing agent design.

---

### Frontend

The frontend is a **thin client**: no LLM keys, no direct agent logic.

**Responsibilities:**

| Concern | Detail |
|---|---|
| **Capture input** | Text area (or guided form) for the travel request; optional examples from the problem statement |
| **Call backend** | `POST /api/plan` with loading state; display disclaimer that the plan is illustrative |
| **Render output** | Sections aligned with product goals: day-by-day outline, neighborhoods/stay areas, inter-city logistics, budget breakdown, review status (pass / warnings / blocking issues) |
| **Resilience** | Handle network errors, HTTP 4xx/5xx, and timeout messaging; optional retry for idempotent plan requests |
| **Developer experience** | Shared types or OpenAPI-generated client from the same contract as backend schemas where practical |

> **Deployment sketch:** Frontend as static assets (CDN or object storage behind CDN); backend as container or PaaS function with outbound access to LLM and tools. Environment-specific API base URL is configured in the frontend build.

---

## System Context

**External dependencies (conceptual):**
- LLM(s) for each agent role
- Optional web search
- Static or sample hotel/transit/price data where real APIs are unavailable
- Currency conversion for budget checks

---

## Logical Architecture — Agents and Responsibilities

| Component | Responsibility | Primary Outputs |
|---|---|---|
| **Orchestrator (Part A — Extraction)** | Parse natural language request → structured constraints (`TravelConstraints`) | `TravelConstraints` |
| **Orchestrator (Part B — Merge)** | Concurrently dispatch constraints to parallel workers; resolve conflicts across catalog, lodging/movement, and budget into `DraftItinerary` | `DraftItinerary` |
| **Orchestrator (Part C — Repair & Final)** | Pass draft to Review Agent; drive repair loop (max 2–3 cycles) on review issues; format user-facing final itinerary | `FinalItinerary` (with disclaimers & trace ID) |
| **Destination Research** | Places, food, temples, experiences; crowd-aware options; must-do vs nice-to-have | `ActivityCatalog`, neighborhood notes, preference-aligned suggestions |
| **Logistics** | Stays per city, inter-city transport, daily ordering, travel-time sanity, backtracking reduction | `LodgingPlan`, `MovementPlan`, `DaySkeleton[]` |
| **Budget** | Category split (stay / transport / food / activities); totals vs cap; cheaper alternatives | `BudgetBreakdown`, flags, `BudgetAdjustments` |
| **Review** | Validate against constraints + realism gate | `ReviewReport` (pass / fail + issues), optional `RepairHints` |

### Pipeline

```
Orchestrator (Part A) → parallel(Destination, Logistics, Budget) → Orchestrator (Part B: Merge) → Review → Orchestrator (Part C: Repair & Output)
```

The orchestrator produces a shared constraint object early (Part A); synthesis happens after parallel agents return (Part B); repair and final formatting happen after Review (Part C).

---

## Orchestration Flow

**How agents communicate:** There is **no** Destination ↔ Logistics ↔ Budget messaging. Each specialist:

1. **Orchestrator Part A** extracts `TravelConstraints` from raw user text.
2. Parallel workers (Destination, Logistics, Budget) receive the same **read-only** `TravelConstraints`.
3. Each worker returns one **typed artifact** to the Orchestrator.
4. **Orchestrator Part B** merges worker artifacts into `DraftItinerary` and sends that (+ constraints) to Review.
5. Review returns `ReviewReport` (and optional `RepairHints`) to the Orchestrator.
6. **Orchestrator Part C** drives repair retries (max 2–3 cycles) upon failures and outputs `FinalItinerary`.

### Communication Topology (Hub-and-Spoke)

```
                    ┌───────────────────────────┐
                    │   Orchestrator (Part A)   │ ← Extract TravelConstraints
                    └─────────────┬─────────────┘
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │  Destination │        │  Logistics   │        │    Budget    │
  │   Research   │        │    Agent     │        │    Agent     │
  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
         └────────────────────────┴───────────────────────┘
                                  │
                          ┌───────▼──────────────────┐
                          │  Orchestrator (Part B)   │ ← Merge into DraftItinerary
                          └───────┬──────────────────┘
                                  │
                          ┌───────▼──────────────────┐
                          │       Review Agent       │
                          └───────┬──────────────────┘
                                  │ ReviewReport / RepairHints
                          ┌───────▼──────────────────┐
                          │  Orchestrator (Part C)   │ ← Repair loop & FinalItinerary
                          └───────┬──────────────────┘
                                  │
                           FinalItinerary
```

> Only the Orchestrator routes messages. Review **never** invokes workers directly — only the Orchestrator does, after interpreting `ReviewReport` / `RepairHints`.

---

## Design Notes

- **Parallel agents share the same read-only `TravelConstraints`** — they must not each re-parse the raw user string differently (avoids inconsistent duration/cities/budget).
- **Merge point is orchestrator-owned:** Destination suggests *what*; Logistics sequences *when* and *where*; Budget may trim or substitute items — conflicts resolved in one place.
- **Review is a hard gate** before user delivery; optional repair loop (orchestrator adjusts, re-runs Review) keeps quality without infinite loops (e.g. max 2–3 cycles).

---

## Core Data Model (Shared Artifacts)

Contracts between agents; implementation can use JSON Schema, Pydantic, or equivalent.

### `TravelConstraints` *(Orchestrator output → input to all workers)*
```
destination_region
cities[]
duration_days
budget_total
currency
preferences[]
avoidances[]           # e.g. crowds
hard_requirements[]    # vs soft_preferences (if inferred)
```

### `ActivityCatalog` *(Destination Agent)*
```
Per city:
  activities[]
    type               # temple, food, etc.
    estimated_duration
    crowd_level        # ordinal or tag
    cost_band
    must_do            # bool
    rationale
```

### `LodgingPlan` + `MovementPlan` *(Logistics Agent)*
```
nights_per_city / area
suggested_neighborhoods  # aligned with Destination
inter_city_mode          # e.g. Shinkansen
DaySkeleton[]
  ordered_slots[]
    travel_time_estimate_between_slots
```

### `BudgetBreakdown` *(Budget Agent)*
```
per_category_totals
per_day_rollup         # optional
within_budget          # bool
violations[]
suggested_swaps[]      # e.g. cheaper Tokyo area
```

### `DraftItinerary` *(Orchestrator merge)*
```
day_by_day[]
  narrative
  structured_slots[]   # linked to ActivityCatalog IDs
budget_summary         # embedded or referenced
```

### `ReviewReport` *(Review Agent)*
```
checklist:
  days_match           # bool
  cities_included      # bool
  within_budget        # bool
  preferences_met      # bool
  crowd_avoidance_effort # bool
  logistics_realism    # bool
issues[]
  severity             # blocking | advisory
```

> **Stable IDs** on activities and lodging suggestions make merge and re-review deterministic.

---

## Agent Interfaces (Minimal API Shape)

Each agent is a function or service with:

- **Input:** `TravelConstraints` + role-specific brief
- **Output:** One primary artifact (above) + optional `confidence` / `assumptions[]`

**Orchestrator additionally exposes:**
```
plan(request) -> FinalItinerary

Internal:
  merge(catalog, logistics, budget) -> DraftItinerary
```

**Review** optionally returns `RepairHints` (e.g. *"remove one full-day Kyoto block"* / *"increase Shinkansen buffer"*) for the orchestrator to apply programmatically or via LLM.

---

## Tooling Layer (Capabilities, Not Agents)

Tools are kept **separate from agent personas** so implementations can be swapped independently.

| Tool Category | Used By | Examples |
|---|---|---|
| **Search / retrieval** | Destination (mainly) | Web search, curated snippets |
| **Geo / routing** | Logistics | Distances, rough transit times |
| **Pricing** | Budget (+ Logistics for transport bands) | Hotel/food/activity ranges or static tables |
| **FX** | Budget | Currency conversion to a single reporting currency |

> Agents call tools through a **single tool router** with logging, timeouts, and caching (same query → same snippet) to control cost and variance.

---

## Execution and Deployment Views

### Full Stack

- **Backend process** (or serverless bundle) hosts the API and MAS; scales on CPU/LLM wait time and concurrent requests.
- **Frontend** is static or edge-hosted; scales cheaply via CDN. Build pipeline produces assets pointing at the correct API base URL per environment (dev/stage/prod).

### Logical Deployment

| Variant | Description |
|---|---|
| **Monolith** | One process runs orchestration + agent prompts in sequence/parallel (async tasks) — acceptable for demos |
| **Scalable** | Orchestrator as workflow engine (e.g. step functions / queue); each agent as stateless worker reading/writing versioned `PlanState` in a store |

### Concurrency
- **Parallel phase:** Three LLM calls (or three subgraphs) with shared constraints and idempotency keys on persisted state.

### State

| Mode | Description |
|---|---|
| **Ephemeral** | In-memory for demos |
| **Durable** | Store `TravelConstraints`, each agent output, each `DraftItinerary` version, and `ReviewReport` for audit and debugging |

---

## Non-Functional Architecture

| Concern | Approach |
|---|---|
| **Latency** | Parallelize Destination / Logistics / Budget; cap tool calls per agent; stream orchestrator narrative if UX needs it |
| **Cost** | Smaller models for Review checklist + structured extraction; larger model for merge/narrative only |
| **Determinism** | Structured outputs (JSON schema); low temperature for Review and constraint extraction |
| **Safety** | No real PII required; disclaimers that plans are illustrative; no guaranteed prices |
| **Observability** | Trace ID per request; log prompts, tool calls, parsed artifacts, Review outcome |
| **Failure** | Per-agent timeout → partial plan with explicit "missing logistics" section; or retry single agent |

---

## Review Agent — Internal Design

Treat Review as **two layers:**

1. **Programmatic checks** *(cheap, reliable)*
   - `duration_days == len(days)`
   - `cities ⊆ plan`
   - `numeric_budget ≤ cap` (using Budget's numbers)

2. **LLM qualitative checks** *(prefs, crowd avoidance, narrative coherence)*
   - Structured rubric → `ReviewReport`

> If programmatic checks fail, you can skip or shorten the LLM pass and still return actionable errors.

---

## Optional Extensions *(Out of Minimal Scope)*

- Human-in-the-loop after Review failure
- Specialist sub-agents (e.g. "temples only") behind Destination for modularity
- RAG over internal travel guides instead of open web
- Separate "Presenter" agent that only formats markdown for UI, keeping policy logic out of prose generation

---

## Summary

The architecture centers on a **constraint-first orchestrator**, three **parallel specialists** (experiences, logistics, money), a **merge step** into a draft itinerary, and a **Review gate** with optional repair loops. Shared typed artifacts between steps keep agents aligned and make validation and debugging straightforward for a PM-friendly demo of multi-agent collaboration.

The **backend** encapsulates all agent and tool execution behind a small HTTP API; the **frontend** provides request entry and structured presentation of the plan, staying free of secrets and heavy business logic.
