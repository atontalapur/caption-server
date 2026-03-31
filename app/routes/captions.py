"""
POST /captions — accepts an image, returns 5 style-matched captions.
Returns 503 if /train has not been called yet.
"""

import io

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.dependencies import limiter
from app.models.schemas import CaptionResponse
from app.services.claude_client import generate_captions

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
    if not request.app.state.trained:
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

    # Verify actual image bytes — do not trust the caller-supplied Content-Type.
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            detected_format = img.format or ""
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=415, detail="File could not be decoded as a valid image.")

    actual_mime = _FORMAT_TO_MIME.get(detected_format, "")
    if actual_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image format. Use JPEG, PNG, GIF, or WebP.",
        )

    try:
        captions = generate_captions(
            image_bytes,
            actual_mime,
            request.app.state.style_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Caption generation failed.")

    return CaptionResponse(
        captions=captions,
        style_samples_loaded=request.app.state.style_samples_count,
    )
