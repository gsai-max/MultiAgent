# Deployment Plan: AI Travel Planner Multi-Agent System

> **Complements:** [`ImplementationPlan.md`](./ImplementationPlan.md) · [`Architecture.md`](./Architecture.md)
> **Target Environment:** Staging & Production Containerized Deployment

---

## Overview

This document outlines the end-to-end production deployment plan for the **AI Travel Planner** multi-agent application. The architecture consists of a stateless **FastAPI Backend** (orchestrator, LLM extraction engine, specialist agents, tool router, and review gate) and a **Web Frontend UI** (Phase 9 presentation layer).

---

## 1. System Requirements & Secrets

### Infrastructure & Runtime
- **Backend Runtime:** Python 3.11+ / Docker 24.0+
- **Frontend Target:** Node.js 18+ static host (Vercel, Netlify, Cloudflare Pages, or Nginx container)
- **Port Bindings:** Backend `8000` (internal container port), Frontend `3000` / `80`

### Environment Variables Matrix

| Variable | Scope | Description | Example (Production) |
|---|---|---|---|
| `HOST` | Backend | Server bind address | `0.0.0.0` |
| `PORT` | Backend | Internal server port | `8000` |
| `CORS_ORIGINS` | Backend | Allowed CORS origins for API security | `https://travel.yourdomain.com,https://app.yourdomain.com` |
| `LLM_API_KEY` | Backend | Secure LLM API credentials (Gemini / OpenAI) | `AIzaSy...` (Secret Manager) |
| `LLM_MODEL` | Backend | Target LLM model name | `gemini-2.5-flash` |
| `VITE_API_URL` | Frontend | Backend public API URL | `https://api-travel.yourdomain.com` |

> [!CAUTION]
> `LLM_API_KEY` must **NEVER** be committed to source control or exposed in frontend client bundles. It must reside strictly in server environment secrets.

---

## 2. Containerization Strategy

### Backend `Dockerfile`
A multi-stage, non-root lightweight Docker image:

```dockerfile
# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Minimal Runtime
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

COPY --from=builder /root/.local /root/.local
COPY backend /app/backend

EXPOSE 8000

# Run non-root user
USER nobody

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production `docker-compose.yml`
For local staging or single-node production deployment:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: travel_planner_backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - CORS_ORIGINS=http://localhost:3000,https://travel.yourdomain.com
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_MODEL=${LLM_MODEL:-gemini-2.5-flash}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## 3. Production Deployment Architecture

The application is deployed using a decoupled stack:
- **Backend API:** Deployed on **Render** as a Python Web Service.
- **Frontend Web UI:** Deployed on **Vercel** as a static Node.js / React single-page application.

---

### A. Backend Deployment: Render (`render.yaml`)

The backend API service is deployed on **Render** using the blueprint configuration file at the repository root [`render.yaml`](file:///c:/Nextleap%20Projects%20Git/MultiAgent/render.yaml):

```yaml
services:
  - type: web
    name: ai-travel-planner-backend
    runtime: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: HOST
        value: 0.0.0.0
      - key: CORS_ORIGINS
        value: http://localhost:3000,http://localhost:5173,https://ai-travel-planner.vercel.app
      - key: LLM_API_KEY
        sync: false
      - key: LLM_MODEL
        value: gemini-2.5-flash
    healthCheckPath: /health
```

#### Step-by-Step Backend Deploy (Render)
1. **Connect Repository:** Log in to [Render Dashboard](https://dashboard.render.com/) and connect the GitHub repository.
2. **New Blueprint:** Select **New Blueprint** and choose the `MultiAgent` repository. Render automatically reads `render.yaml`.
3. **Set Secrets:** Under Environment Variables, input your secure `LLM_API_KEY`.
4. **Deploy:** Click **Apply**. Render builds the service and exposes a public HTTPS URL (e.g., `https://ai-travel-planner-backend.onrender.com`).

---

### B. Frontend Deployment: Vercel

The frontend Web UI is deployed on **Vercel** with automatic deployment on push to `main`.

#### Configuration Settings (Vercel Dashboard)
- **Framework Preset:** Vite / React or Next.js
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist` (or `.next`)

#### Environment Variables (Vercel)
| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://ai-travel-planner-backend.onrender.com` |

#### Step-by-Step Frontend Deploy (Vercel)
1. **Import Project:** Log in to [Vercel Dashboard](https://vercel.com/) and click **Add New > Project**.
2. **Select Repository:** Choose `MultiAgent` and set Root Directory to `frontend`.
3. **Configure Environment Variables:** Add `VITE_API_URL` pointing to your Render backend URL.
4. **Deploy:** Click **Deploy**. Vercel generates a production URL (e.g., `https://ai-travel-planner.vercel.app`).

---



## 4. CI/CD Automated Pipeline

Create `.github/workflows/deploy.yml` for automated testing and deployment:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Run Pytest Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt pytest anyio

      - name: Execute Pytest Suite across all Phases
        env:
          PYTHONPATH: .
        run: pytest -v

  deploy:
    name: Deploy to Production
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & Deploy Container Image
        run: |
          echo "Deploying container image to Cloud Run / ECS..."
```

---

## 5. Health Monitoring & Observability

- **Health Check Endpoint:** `GET /health` returns HTTP 200 `{ "status": "ok", "service": "ai-travel-planner-backend" }`.
- **Trace Propagation:** Every request logs a unique `X-Trace-ID` header.
- **Logging Standards:** Structured JSON logs sent to standard output (`stdout`) for aggregation by CloudWatch / Datadog.

---

## 6. Rollback & Recovery Strategy

1. **Zero-Downtime Rolling Deployment:** New container revisions start and pass 3 consecutive `/health` checks before routing live traffic.
2. **Automated Rollback:** If `/health` or `POST /api/plan` error rates exceed 1% over 2 minutes, traffic automatically rolls back to the previous stable container tag.
3. **Graceful Fallback Resilience:** In-app per-agent timeouts (`15s`) handle transient API latency without crashing worker threads.
