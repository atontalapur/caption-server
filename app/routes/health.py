"""
GET /health — liveness + training status check.
"""

import logging

from fastapi import APIRouter, Request

from app.dependencies import limiter
from app.models.schemas import HealthResponse

log = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health(request: Request):
    return HealthResponse(
        status="ok",
        trained=request.app.state.trained,
        files_loaded=request.app.state.style_samples_count,
    )
