"""
POST /captions — accepts an image, returns 5 style-matched captions.

Style context is loaded fresh from disk on every request so that the
endpoint stays correct under multi-worker deployments (each worker has
its own app.state, but all share the same persistent cache file).
"""

import asyncio
import io
import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.dependencies import limiter
from app.models.schemas import CaptionResponse
from app.services.claude_client import generate_captions
from app.services.style_loader import load_style

log = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MB

_FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "GIF": "image/gif",
    "WEBP": "image/webp",
}

router = APIRouter(tags=["captions"])


@router.post("/captions", response_model=CaptionResponse)
@limiter.limit("10/minute")
async def create_captions(request: Request, image: UploadFile = File(...)):
    """
    Upload a photo and receive 5 captions written in the trained style.

    Call **POST /train** first to provide writing samples.
    Supported formats: JPEG, PNG, GIF, WebP (max 20 MB).
    """
    # Reload style context from disk so this worker always has current data,
    # even if a different worker handled the most recent /train call.
    samples, style_context = load_style()
    if not samples:
        raise HTTPException(
            status_code=503,
            detail=(
                "The server has not been trained yet. "
                "Call POST /train with your writing samples first."
            ),
        )

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Image file is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 20 MB limit.")

    # Verify actual image bytes off the event loop — do not trust caller-supplied
    # Content-Type, and avoid blocking the event loop with CPU-bound Pillow work.
    def _decode_image() -> str:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            return img.format or ""

    try:
        detected_format = await asyncio.to_thread(_decode_image)
    except (UnidentifiedImageError, OSError, IOError):
        raise HTTPException(status_code=415, detail="File could not be decoded as a valid image.")

    actual_mime = _FORMAT_TO_MIME.get(detected_format, "")
    if actual_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Use JPEG, PNG, GIF, or WebP.",
        )

    log.info("Caption request: format=%s size=%d bytes", detected_format, len(image_bytes))

    try:
        captions = generate_captions(image_bytes, actual_mime, style_context)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        log.exception("Unexpected error during caption generation")
        raise HTTPException(status_code=500, detail="Caption generation failed.")

    return CaptionResponse(
        captions=captions,
        style_samples_loaded=len(samples),
    )
