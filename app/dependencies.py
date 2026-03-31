"""
Shared FastAPI dependencies: rate limiter and API-key auth.
"""

import os
from fastapi import Header, HTTPException, Request
from slowapi import Limiter


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP, honouring X-Forwarded-For set by reverse proxies
    (standard on Hugging Face Spaces and most cloud platforms).
    Falls back to the raw socket address when the header is absent.
    """
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# app.state.limiter must be set to this instance before any route is registered.
# This is done in main.py (module level, before include_router calls).
limiter = Limiter(key_func=_get_client_ip)

_TRAIN_KEY = os.getenv("TRAIN_API_KEY", "").strip()


async def require_train_key(authorization: str = Header(default="")) -> None:
    """
    Enforce Bearer-token auth on write endpoints when TRAIN_API_KEY is set.

    If TRAIN_API_KEY is not configured (or blank) the server starts in open
    mode and this dependency is a no-op (a startup warning is printed by
    main.py).
    """
    if not _TRAIN_KEY:
        return
    if authorization != f"Bearer {_TRAIN_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
