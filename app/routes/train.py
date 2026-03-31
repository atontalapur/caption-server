"""
POST /train — one-time call to upload writing samples.

Send the entire training directory as a multipart file list.
After this returns 200, the server is ready to caption images.

Calling /train again replaces the previous training data.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.dependencies import limiter, require_train_key
from app.models.schemas import TrainResponse
from app.services.style_loader import (
    build_style_context,
    extract_text_from_uploads,
    save_style,
)

log = logging.getLogger(__name__)

router = APIRouter(tags=["training"])

ACCEPTED_EXTENSIONS = {".txt", ".md", ".mdx"}
MAX_FILE_BYTES = 1 * 1024 * 1024  # 1 MB per file


@router.post("/train", response_model=TrainResponse, dependencies=[Depends(require_train_key)])
@limiter.limit("5/hour")
async def train_model(
    request: Request,
    files: List[UploadFile] = File(..., description="All files from your writings directory"),
):
    """
    Upload your writing samples to prime the caption style.

    - Send every `.txt`, `.md`, or `.mdx` file from your writings folder.
    - Files larger than 1 MB or non-text types are rejected/skipped.
    - Call this once before sending images. Calling again replaces the style.
    - Requires `Authorization: Bearer <TRAIN_API_KEY>` when `TRAIN_API_KEY` is set.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    filenames: list[str] = []
    contents: list[bytes] = []

    for f in files:
        raw = await f.read()
        if len(raw) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File '{f.filename}' exceeds the 1 MB per-file limit "
                    f"({len(raw) / 1024:.0f} KB)."
                ),
            )
        filenames.append(f.filename or "")
        contents.append(raw)

    samples, accepted = extract_text_from_uploads(filenames, contents)

    if accepted == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"None of the {len(files)} uploaded file(s) were readable text files. "
                f"Accepted extensions: {', '.join(sorted(ACCEPTED_EXTENSIONS))}"
            ),
        )

    # Acquire per-worker lock so concurrent /train calls don't interleave
    # disk writes or leave app.state in a partially-updated state.
    async with request.app.state.train_lock:
        save_style(samples)
        style_context = build_style_context(samples)

        # Update in-memory state only after all I/O is complete.
        request.app.state.style_context = style_context
        request.app.state.style_samples_count = accepted
        request.app.state.trained = True

    log.info("Training updated: %d file(s) accepted, context_chars=%d", accepted, len(style_context))

    return TrainResponse(
        status="ready",
        files_accepted=accepted,
        message=(
            f"Training data accepted ({accepted} file(s)). "
            "The server is now ready to generate captions."
        ),
    )
