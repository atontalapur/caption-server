"""
Shared FastAPI dependencies: rate limiter and API-key auth.
"""

import os

from fastapi import Header, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

_TRAIN_KEY = os.getenv("TRAIN_API_KEY", "")


async def require_train_key(authorization: str = Header(default="")) -> None:
    """
    Enforce Bearer-token auth on write endpoints when TRAIN_API_KEY is set.

    If TRAIN_API_KEY is not configured the server starts in open mode and
    this dependency is a no-op (a startup warning is printed by main.py).
    """
    if not _TRAIN_KEY:
        return
    if authorization != f"Bearer {_TRAIN_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
