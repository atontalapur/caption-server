"""
Caption Server — entry point.
Default port: 7860 (Hugging Face Spaces standard).
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import captions, health, train
from app.services.style_loader import load_style

load_dotenv()

PORT = int(os.getenv("PORT", "7860"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Restore any previously saved training data
    samples, style_context = load_style()

    app.state.style_context = style_context
    app.state.style_samples_count = len(samples)
    app.state.trained = len(samples) > 0
    app.state.port = PORT

    if app.state.trained:
        print(
            f"[caption-server] Restored {len(samples)} writing sample(s) from cache. "
            "Ready to caption images."
        )
    else:
        print(
            "[caption-server] No training data found. "
            "Call POST /train with your writing samples before sending images."
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

# Open CORS so any application (Next.js, mobile, scripts, etc.) can call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(train.router)
app.include_router(captions.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)
