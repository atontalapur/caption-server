"""
Caption Server — entry point.
Default port: 7860 (Hugging Face Spaces standard).
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import limiter
from app.routes import captions, health, train
from app.services.style_loader import check_storage_writable, load_style

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "7860"))

# Comma-separated list of allowed origins, e.g. "https://myapp.com,https://other.com".
# Defaults to "*" so local / HF Spaces usage works out of the box, but should be
# restricted in production.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Storage writability check — warns early if /app/data is not persistent.
    check_storage_writable()

    samples, style_context = load_style()

    # app.state is used as a warm-start cache only.
    # Captions routes re-read from disk to stay correct under multi-worker deploys.
    app.state.style_context = style_context
    app.state.style_samples_count = len(samples)
    app.state.trained = len(samples) > 0

    # Mutex for concurrent /train requests (per-worker).
    app.state.train_lock = asyncio.Lock()

    if app.state.trained:
        log.info("Restored %d writing sample(s) from cache. Ready to caption images.", len(samples))
    else:
        log.info("No training data found. Call POST /train with writing samples before sending images.")

    if not os.getenv("TRAIN_API_KEY", "").strip():
        log.warning(
            "TRAIN_API_KEY is not set. POST /train is open to any caller — "
            "set this env var in production."
        )

    yield


app = FastAPI(
    title="Caption Server",
    description=(
        "Generates 5 photo captions in your personal writing style via Claude vision.\n\n"
        "**Workflow:**\n"
        "1. `POST /train` — upload your writing samples (one-time setup).\n"
        "2. `POST /captions` — send any photo, receive 5 captions."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# limiter must be assigned to app.state before include_router calls so that
# slowapi can find it when decorating route handlers.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(train.router)
app.include_router(captions.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)
