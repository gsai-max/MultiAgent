# Edge Case Analysis & Exception Handling Guide: AI Travel Planner

> **Complements:** [`ProblemStatement.txt`](./ProblemStatement.txt) · [`Context.md`](./Context.md) · [`Architecture.md`](./Architecture.md) · [`ImplementationPlan.md`](./ImplementationPlan.md) · [`DeploymentPlan.md`](./DeploymentPlan.md)
> **Scope:** Multi-Agent System Exception Scenarios & Mitigation Strategies

---

## Overview

In real-world travel planning, user inputs, external tool calls, and LLM responses exhibit high ambiguity, missing data, and unexpected constraints. This document details all potential **edge cases** across the 5 specialized agents, orchestrator pipeline segments, review gates, and deployment layers, along with their programmatic mitigations.

---

## 1. Input & Extraction Edge Cases (Orchestrator Part A)

### 1.1 Unrealistic Budget Caps
- **Scenario:** User requests a 10-day trip to Tokyo with a total budget cap of `$50`.
- **System Failure Risk:** Budget Agent produces negative allowances or fails reconciliation pass; Review Gate repeatedly rejects draft.
- **Mitigation:**
  - `ConstraintExtractor` enforces baseline minimum thresholds per region/day.
  - If budget is below regional baseline, `BudgetAgent` flags a hard violation upfront and populates `suggested_swaps` with hostel/budget recommendations.
  - If unresolvable within budget cap, `FinalItinerary` reports a non-blocking advisory notice with clear overage breakdown instead of crashing.

### 1.2 Minimally Specified or Ambiguous Requests
- **Scenario:** User submits `"Plan a trip somewhere nice"` (missing duration, cities, budget, or region).
- **System Failure Risk:** Null pointer / key errors in specialist agents expecting mandatory fields.
- **Mitigation:**
  - `TravelConstraints` schema enforces strict Pydantic defaults (e.g. `duration_days` defaults to 5, `budget_total` defaults to $3,000, `currency` defaults to `USD`).
  - `ConstraintExtractor` fills missing fields with sensible travel defaults and logs extraction confidence notes.

### 1.3 Contradictory Preferences & Avoidances
- **Scenario:** User requests `"I want to visit Shibuya Crossing and popular night markets, but I strictly hate all crowds."`
- **System Failure Risk:** Destination Agent cannot satisfy both preference (Shibuya) and avoidance (crowds).
- **Mitigation:**
  - `DestinationAgent` prioritizes crowd avoidance by scheduling high-crowd attractions during off-peak windows (e.g. early morning 7:00 AM visits or late evening strolls).
  - Notes are attached to catalog items explaining how off-peak timing resolves the contradiction.

### 1.4 Single-Day or Long-Duration Extremes
- **Scenario:** 1-day trip (0 nights stay) or 30-day multi-city trip request.
- **System Failure Risk:** Division by zero in night-stay allocation; excessive token lengths exceeding LLM context limits.
- **Mitigation:**
  - 1-day trips set `nights_per_city = 0` and skip inter-city transit.
  - Long trips (>14 days) aggregate daily slots into city block skeletons to maintain token budget within LLM context windows.

---

## 2. Specialist Worker Agent Edge Cases (Phase 4)

### 2.1 Destination Agent: Zero Search Results / Niche Queries
- **Scenario:** Query for a rare interest tag in a small town returns empty search snippets.
- **System Failure Risk:** Empty `ActivityCatalog.activities` list; empty day skeletons downstream.
- **Mitigation:**
  - `DestinationAgent._build_stub_catalog` fallback provides curated regional activities (historical strolls, culinary dining) whenever search returns zero items.

### 2.2 Logistics Agent: Unrealistic Inter-City Transit / Single-City Multi-Nights
- **Scenario:** User requests 3 cities in 2 days (e.g. Tokyo -> Kyoto -> Osaka in 48 hours).
- **System Failure Risk:** Travel time consumes 80%+ of waking hours; day schedule becomes unachievable.
- **Mitigation:**
  - `LogisticsAgent` calculates transit duration via `ToolRouter.geo_estimate`.
  - If inter-city transit exceeds 4 hours in a short trip, `LogisticsAgent` consolidates nights in the primary hub city and issues a transit advisory note.

### 2.3 Budget Agent: Extreme Currency & FX Band Fluctuations
- **Scenario:** Request in non-USD currencies (JPY, EUR, GBP) or missing FX benchmark rates.
- **System Failure Risk:** FX conversion error causes miscalculated budget status.
- **Mitigation:**
  - `ToolRouter.fx_convert` provides static FX conversion fallback rates when external conversion rates are offline.
  - All category spend calculations are normalized to `USD` internally before final currency formatting.

---

## 3. Orchestrator Merge & Scheduling Edge Cases (Phase 5)

### 3.1 Unlinked Slot Activity IDs
- **Scenario:** `LogisticsAgent` creates a `DaySlot` with `activity_id = null` or an ID missing from `ActivityCatalog`.
- **System Failure Risk:** Broken references in UI rendering; uncounted activity spend in budget breakdown.
- **Mitigation:**
  - `OrchestratorService.merge()` scans unassigned slots and links them to available catalog items matching the same city and time-of-day category.

### 3.2 Over-Scheduling & Time Slot Overlap
- **Scenario:** 5 catalog activities assigned to a single afternoon slot.
- **System Failure Risk:** Day schedule total duration exceeds waking hours (>12 hours).
- **Mitigation:**
  - `merge()` caps activity slots to a maximum of 3 slots per day (Morning, Afternoon, Evening) with built-in travel buffer times (`travel_time_from_prev_minutes`).

---

## 4. Review Gate & Bounded Repair Loop Edge Cases (Phase 6 & 7)

### 4.1 Exhaustion of Maximum Repair Cycles (`max_repairs = 2`)
- **Scenario:** Review Gate flags blocking issues (e.g. spend > budget cap), but repair actions fail to bring spend within cap after 2 retries.
- **System Failure Risk:** Infinite execution loop or server crash.
- **Mitigation:**
  - Bounded retry loop (`while not passed and repair_count < max_repairs:`) strictly terminates after `max_repairs` iterations.
  - Returns `FinalItinerary` with logged `repair_history`, explicit warning checklist, and non-blocking disclaimer notice.

### 4.2 Structural Day Schedule Mismatches
- **Scenario:** Initial merged draft has 3 days, but `TravelConstraints` specified 5 days.
- **System Failure Risk:** `ReviewAgent` flags `days_match = False`.
- **Mitigation:**
  - `OrchestratorService.apply_repairs()` automatically appends additional day skeletons for the primary destination city to achieve exact day count alignment.

---

## 5. System Resilience & Deployment Edge Cases (Phase 8 & Render/Vercel)

### 5.1 Worker Agent Timeout / Rate Limiting (Groq / LLM API 429)
- **Scenario:** Groq API rate limit or network timeout occurs during parallel execution of Destination or Logistics agents.
- **System Failure Risk:** HTTP 500 error returned to end user.
- **Mitigation:**
  - Parallel execution tasks are wrapped in `asyncio.wait_for(..., timeout=15.0)`.
  - If a worker agent times out or fails, safe fallback builders (`_build_stub_catalog`, `_build_stub_logistics`, `_build_stub_budget`) execute seamlessly, enabling the pipeline to deliver a valid response.

### 5.2 Malformed LLM Output (Invalid JSON Schema)
- **Scenario:** LLM response contains trailing prose, unescaped quotes, or missing fields.
- **System Failure Risk:** Pydantic `ValidationError` or `JSONDecodeError`.
- **Mitigation:**
  - `LLMClient.clean_json_string()` strips markdown fences (` ```json ... ``` `).
  - Single-retry repair loop in `LLMClient.extract_structured` feeds the exact validation error back to the LLM for self-correction.

### 5.3 CORS & Cross-Origin Frontend Integration
- **Scenario:** Web UI on Vercel (`https://ai-travel-planner.vercel.app`) calls backend on Render (`https://ai-travel-planner-backend.onrender.com`).
- **System Failure Risk:** Browser blocks API call due to CORS preflight error.
- **Mitigation:**
  - FastAPI `CORSMiddleware` in `main.py` explicitly allows allowed origins (`CORS_ORIGINS`), headers, and credentials.

---

## 6. Summary Matrix: Edge Cases & Mitigations

| Category | Edge Case | Mitigation Strategy | Owner Component |
|---|---|---|---|
| **Input** | Missing / Minimal Request Data | Pydantic field defaults + fallback extraction | `ConstraintExtractor` |
| **Input** | Unrealistic Budget Cap | Baseline cost floors + cost-saving swaps | `BudgetAgent` |
| **Worker** | Search API Timeout / Rate Limit | 15s timeout wrapper + deterministic stub fallbacks | `OrchestratorService` |
| **Worker** | Malformed LLM Output | Regex cleaning + 1-retry repair loop | `LLMClient` |
| **Merge** | Unlinked Activity Slot IDs | Auto-linking to city catalog items in `merge()` | `OrchestratorService` |
| **Review** | Unresolved Repair Issues | Bounded retry loop (`max_repairs=2`) + advisory report | `OrchestratorService` |
| **Deploy** | Cross-Origin Browser Errors | Explicit `CORSMiddleware` header configuration | `main.py` / `config.py` |
