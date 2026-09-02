import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ai_travel_planner.trace")

class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-ID") or f"trace-{uuid.uuid4().hex[:12]}"
        request.state.trace_id = trace_id

        logger.info(f"[TraceID: {trace_id}] Incoming request: {request.method} {request.url.path}")

        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id

        logger.info(f"[TraceID: {trace_id}] Completed request: status {response.status_code}")
        return response
