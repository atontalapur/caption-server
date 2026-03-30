"""
Handles writing-style context: building it from uploaded files
and persisting it so the server survives restarts.
"""

import json
import os
from pathlib import Path
from typing import List, Tuple

SUPPORTED_EXTENSIONS = {".txt", ".md", ".mdx"}
CACHE_PATH = Path(os.getenv("STYLE_CACHE_PATH", "data/style_cache.json"))
MAX_STYLE_CHARS = 6000


# ---------------------------------------------------------------------------
# Build from raw text samples
# ---------------------------------------------------------------------------

def build_style_context(samples: List[str], max_chars: int = MAX_STYLE_CHARS) -> str:
    """Concatenate samples into a single style-context string, capped at max_chars."""
    if not samples:
        return ""
    combined = "\n\n---\n\n".join(samples)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[...truncated for brevity]"
    return combined


def extract_text_from_uploads(
    filenames: List[str],
    file_contents: List[bytes],
) -> Tuple[List[str], int]:
    """
    Parse uploaded bytes into text samples.

    Returns (samples, accepted_count) where accepted_count is the number
    of files whose extension was recognised and content was non-empty.
    """
    samples: List[str] = []
    for name, content in zip(filenames, file_contents):
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue
        try:
            text = content.decode("utf-8").strip()
            if text:
                samples.append(text)
        except (UnicodeDecodeError, Exception):
            pass  # skip unreadable files
    return samples, len(samples)


# ---------------------------------------------------------------------------
# Persistence  (written to CACHE_PATH)
# ---------------------------------------------------------------------------

def save_style(samples: List[str]) -> None:
    """Persist samples to disk so they survive server restarts."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps({"samples": samples}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_style() -> Tuple[List[str], str]:
    """
    Load persisted samples from disk.

    Returns (samples, style_context).  Both are empty if no cache exists yet.
    """
    if not CACHE_PATH.exists():
        return [], ""
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        samples: List[str] = data.get("samples", [])
        return samples, build_style_context(samples)
    except Exception:
        return [], ""
