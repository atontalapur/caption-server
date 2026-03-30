"""
POST /captions — accepts an image upload, returns 5 style-matched captions.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Request

from app.models.schemas import CaptionResponse
from app.services.claude_client import generate_captions

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20 MB — Claude's limit

router = APIRouter(prefix="/captions", tags=["captions"])


@router.post("", response_model=CaptionResponse)
async def create_captions(request: Request, image: UploadFile = File(...)):
    """
    Upload a photo and receive 5 captions written in the user's style.

    - **image**: The photo file (JPEG, PNG, GIF, or WebP).
    """
    content_type = image.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type '{content_type}'. Use JPEG, PNG, GIF, or WebP.",
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 20 MB limit.",
        )
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    # style_context is preloaded on startup and stored in app state
    style_context: str = request.app.state.style_context
    samples_count: int = request.app.state.style_samples_count

    try:
        captions = generate_captions(image_bytes, content_type, style_context)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Claude API error: {exc}")

    return CaptionResponse(captions=captions, style_samples_loaded=samples_count)
