from fastapi import APIRouter
from backend.app.schemas.plan import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="ai-travel-planner-backend")
