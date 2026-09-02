# AI Travel Planner — Frontend Application (Phase 9)

Web UI for **AI Travel Planner** built with React, TypeScript, Vite, Lucide Icons, and custom glassmorphism styling.

## Features
- **Natural Language Request Form**: Textarea input with character counter and quick example preset chips.
- **Multi-Agent Pipeline Visualizer**: Live step-by-step progress indicator reflecting backend extraction, parallel specialist agents, orchestrator merge, and review quality gate.
- **Cancel Request Support**: Integrated `AbortController` signal handling to cancel pending plan generation calls.
- **Interactive Itinerary Presentation**:
  - **Overview Header**: Region, duration, total budget cap, cities, and trace ID.
  - **Narrative Overview**: Multi-agent executive summary of the journey.
  - **Day-by-Day Timeline**: Day selector tabs, time-of-day slots (morning, afternoon, evening), transit time from prior slot, and activity details.
  - **Budget Allocation Visualizer**: Spend vs cap progress bar, per-category breakdown, and cost-saving swap suggestions.
  - **Lodging & Logistics**: City stay recommendations, accommodation options, and inter-city movement modes.
  - **Quality Gate Report**: 6-point rule checklist status (days match, cities included, within budget, preferences met, crowd avoidance, logistics realism) and advisory notes.
  - **Prominent Disclaimer Notice**: Mandatory notice on AI-generated travel plans.
  - **Copy Markdown Action**: Export formatted itinerary to clipboard.
- **Structured Error Handling**: Card rendering HTTP status code, trace ID, and retry prompt.

## Setup & Running

### Prerequisites
- Node.js v18+
- Backend API running on `http://127.0.0.1:8000` (or configured via environment)

### Development
```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Run dev server (defaults to http://localhost:5173)
npm run dev
```

### Production Build
```bash
# Compile TypeScript and generate static bundle in dist/
npm run build

# Preview build locally
npm run preview
```

### Environment Variables
- `VITE_API_URL`: Backend API base URL (Default: `http://127.0.0.1:8000` via Vite proxy).
