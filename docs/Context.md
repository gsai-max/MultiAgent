# Context: AI Travel Planner — Multi-Agent System

> **Source:** `ProblemStatement.txt`
> **Project:** Automations & Multi-Agent Systems — Graduation Project
> **Created:** 2026-09-02

---

## 1. Background & Motivation

Travel planning appears simple on the surface but quickly becomes overwhelming due to the number of inter-related decisions a traveler must make simultaneously (destinations, lodging, transport, budget, personal preferences). A system is needed that can take a short, natural-language request and intelligently coordinate multiple specialized tasks to produce a coherent, validated travel plan.

---

## 2. Problem Statement

A traveler submits a natural-language request like:

> *"Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds."*

Solving this well requires combining:
- Understanding traveler goals and preferences
- Researching destinations and attractions
- Comparing hotels and transport options
- Enforcing budget constraints
- Verifying that the final itinerary actually satisfies the original request

---

## 3. Objective

Design a **Travel Planning Multi-Agent System** that automatically converts a short travel request into a usable trip plan. The goal is **not** to build a production travel product, but to **demonstrate how multiple specialized AI agents collaborate** on a real-world problem that is intuitive for product managers.

---

## 4. Expected System Output

Given a travel request, the system should produce:

| Output | Description |
|---|---|
| Day-by-day trip outline | A sequenced itinerary for each day of the trip |
| Neighborhood recommendations | Suggested areas to stay in each city |
| Travel logistics | How to move between cities and manage daily routing |
| Budget breakdown | Cost estimates per category; alternatives where needed |
| Final validated itinerary | A plan that respects all user preferences and constraints |

---

## 5. Multi-Agent System Architecture

### Execution Flow

```
Orchestrator → [Destination Agent + Logistics Agent + Budget Agent] (parallel) → Review Agent
```

---

### Agent 1 — Orchestrator Agent
**Role:** Master planner, task delegator, merger, repair loop driver, and output synthesizer.

**Responsibilities & Structure:**
- **Part A — Constraint Extraction (Phase 2):** Parses the free-form user request and extracts structured `TravelConstraints`:
  - **Destination:** Japan
  - **Duration:** 5 days
  - **Cities:** Tokyo + Kyoto
  - **Budget:** $3,000
  - **Preferences:** Food, temples
  - **Avoidances:** Crowds
- **Part B — Parallel Execution & Merge (Phase 5):** Dispatches constraints concurrently to Destination, Logistics, and Budget agents, then merges specialist outputs into `DraftItinerary`.
- **Part C — Repair Loop & Plan Finalization (Phase 7):** Sends draft itinerary to Review Agent, manages bounded repair retries (max 2–3 cycles) upon review failures, and synthesizes the final user-facing `FinalItinerary`.

---

### Agent 2 — Destination Research Agent
**Role:** Finds the best places, experiences, and food ideas aligned with traveler preferences.

**Inputs:**
- Web search results
- Travel guides
- Restaurant reviews
- Attraction summaries

**Outputs:**
- Recommended neighborhoods, temples, food streets, and local experiences
- Less-crowded alternatives where possible
- Categorization of "must-do" vs "nice-to-have" items

**Example outputs:**
- Best quiet temple areas in Kyoto
- Food neighborhoods in Tokyo
- Off-peak or less-crowded experiences

---

### Agent 3 — Logistics Agent
**Role:** Handles the practical side of travel — accommodation, routes, and daily sequencing.

**Inputs:**
- Hotel APIs or sample hotel data
- Train routes / transit information
- Maps / distance tools

**Outputs:**
- Where to stay in each city
- Estimated travel times between locations
- Inter-city transport recommendations (e.g., Shinkansen)
- Day plans that minimize backtracking

**Example outputs:**
- 2 nights Tokyo → 2 nights Kyoto → 1 flexible day
- Shinkansen recommended for Tokyo–Kyoto leg
- Geographically efficient daily itineraries

---

### Agent 4 — Budget Agent
**Role:** Ensures the entire plan stays within the traveler's stated budget.

**Inputs:**
- Currency conversion data
- Estimated hotel costs
- Food and transport price ranges
- Attraction pricing

**Outputs:**
- Budget broken into categories: Stay, Transport, Food, Activities
- Flags over-budget components
- Suggests cheaper alternatives when needed

**Example outputs:**
- Estimated total spend: $2,650
- Central Tokyo hotel too expensive → suggest alternate area

---

### Agent 5 — Review Agent
**Role:** Quality checker that validates the final itinerary before delivery to the user.

**Validation Criteria:**
- Does the itinerary fit within 5 days?
- Does it include both Tokyo and Kyoto?
- Is the total cost within the $3,000 budget?
- Does it align with "food + temples" preferences?
- Does it avoid or minimize crowded experiences?
- Is the plan realistic from a travel-time perspective?

---

## 6. Key Design Principles

| Principle | Detail |
|---|---|
| **Separation of concerns** | Each agent owns a distinct problem domain |
| **Parallel execution** | Destination, Logistics, and Budget agents run simultaneously |
| **Gate-keeping** | Review Agent acts as a final validation gate before output is shown |
| **Natural language input** | The system accepts free-form user requests |
| **PM-friendly demonstration** | Designed to be easy for non-engineers to understand and evaluate |

---

## 7. Constraints & Scope

- This is a **demonstration system**, not a production travel product
- Focus is on **multi-agent coordination patterns**, not accuracy of real travel data
- The system should handle the specific example request (Japan, 5 days, $3,000) and generalize to similar requests

---

## 8. Reference Example Request

```
"Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds."
```

This serves as the canonical test case for validating the system end-to-end.
