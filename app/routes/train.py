"""
POST /train — one-time call to upload writing samples.

Send the entire training directory as a multipart file list.
After this returns 200, the server is ready to caption images.

Calling /train again replaces the previous training data.
"""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from typing import List

from app.models.schemas import TrainResponse
from app.services.style_loader import (
    build_style_context,
    extract_text_from_uploads,
    save_style,
)

router = APIRouter(tags=["training"])

ACCEPTED_EXTENSIONS = {".txt", ".md", ".mdx"}


@router.post("/train", response_model=TrainResponse)
async def train_model(
    request: Request,
    files: List[UploadFile] = File(..., description="All files from your writings directory"),
):
    """
    Upload your writing samples to prime the caption style.

    - Send every `.txt`, `.md`, or `.mdx` file from your writings folder.
    - Other file types are silently ignored.
    - Call this once before sending images. Calling again replaces the style.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    filenames = [f.filename or "" for f in files]
    contents = [await f.read() for f in files]

    samples, accepted = extract_text_from_uploads(filenames, contents)

    if accepted == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"None of the {len(files)} uploaded file(s) were readable text files. "
                f"Accepted extensions: {', '.join(sorted(ACCEPTED_EXTENSIONS))}"
            ),
        )

    # Persist to disk and update live app state
    save_style(samples)
    request.app.state.style_context = build_style_context(samples)
    request.app.state.style_samples_count = accepted
    request.app.state.trained = True

    return TrainResponse(
        status="ready",
        files_accepted=accepted,
        message=(
            f"Training data accepted ({accepted} file(s)). "
            "The server is now ready to generate captions."
        ),
    )
