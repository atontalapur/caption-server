"""
GET /health — liveness check, useful for Next.js to verify the server is up.
"""

from fastapi import APIRouter, Request
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    return HealthResponse(
        status="ok",
        writings_loaded=request.app.state.style_samples_count,
        port=request.app.state.port,
    )
