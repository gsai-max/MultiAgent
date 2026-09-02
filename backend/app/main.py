import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.middleware.trace import TraceMiddleware
from backend.app.routers import health, plan

from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_travel_planner")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"AI Travel Planner API initialized. Listening on CORS: {settings.cors_origins_list}")
    yield

app = FastAPI(
    title="AI Travel Planner API",
    description="Backend API for AI Travel Planner multi-agent system",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Trace ID Middleware
app.add_middleware(TraceMiddleware)

# Include Routers
app.include_router(health.router)
app.include_router(plan.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
