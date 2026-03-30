"""
POST /captions — accepts an image, returns 5 style-matched captions.
Returns 503 if /train has not been called yet.
"""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.models.schemas import CaptionResponse
from app.services.claude_client import generate_captions

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MB

router = APIRouter(tags=["captions"])


@router.post("/captions", response_model=CaptionResponse)
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

    content_type = image.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type '{content_type}'. Use JPEG, PNG, GIF, or WebP.",
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 20 MB limit.")
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    try:
        captions = generate_captions(
            image_bytes,
            content_type,
            request.app.state.style_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Claude API error: {exc}")

    return CaptionResponse(
        captions=captions,
        style_samples_loaded=request.app.state.style_samples_count,
    )
