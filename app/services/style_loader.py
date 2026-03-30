"""
Loads writing samples from the data/writings directory.
Supports .txt, .md, and .mdx files.
"""

import os
from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {".txt", ".md", ".mdx"}


def load_writings(writings_dir: str) -> List[str]:
    """Read all writing samples from the given directory."""
    path = Path(writings_dir)
    if not path.exists():
        return []

    samples: List[str] = []
    for file in sorted(path.iterdir()):
        if file.suffix.lower() in SUPPORTED_EXTENSIONS and file.is_file():
            try:
                text = file.read_text(encoding="utf-8").strip()
                if text:
                    samples.append(text)
            except Exception:
                pass  # skip unreadable files silently

    return samples


def build_style_context(samples: List[str], max_chars: int = 6000) -> str:
    """
    Concatenate samples into a single style-context string,
    capped at max_chars to stay well within the Claude context window.
    """
    if not samples:
        return ""

    combined = "\n\n---\n\n".join(samples)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[...truncated for brevity]"

    return combined
