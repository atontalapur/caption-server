"""
Caption Server — entry point.
Starts a FastAPI app on PORT (default 8472).
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import captions, health
from app.services.style_loader import build_style_context, load_writings

load_dotenv()

PORT = int(os.getenv("PORT", "8472"))
WRITINGS_DIR = os.getenv("WRITINGS_DIR", "data/writings")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load writing samples once on startup
    samples = load_writings(WRITINGS_DIR)
    app.state.style_context = build_style_context(samples)
    app.state.style_samples_count = len(samples)
    app.state.port = PORT

    loaded = len(samples)
    if loaded:
        print(f"[caption-server] Loaded {loaded} writing sample(s) for style priming.")
    else:
        print(
            "[caption-server] No writing samples found in "
            f"'{WRITINGS_DIR}' — captions will use a default style. "
            "Drop .txt / .md files there and restart to enable style priming."
        )

    yield  # server runs here


app = FastAPI(
    title="Caption Server",
    description="Generates 5 photo captions in the user's personal writing style via Claude.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow Next.js dev (localhost:3000) and any production origin.
# Tighten ALLOW_ORIGINS in production via env var.
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(captions.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
