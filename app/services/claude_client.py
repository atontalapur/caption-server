"""
Claude API client for generating captions from an image
using the user's personal writing style as context.
"""

import base64
import anthropic
from typing import List


_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def _build_system_prompt(style_context: str) -> str:
    base = (
        "You are a creative caption writer. "
        "Your job is to generate exactly 5 captivating, punchy captions for a photo.\n\n"
        "Rules:\n"
        "- Return ONLY a JSON array of 5 strings, nothing else. Example: [\"cap1\", \"cap2\", \"cap3\", \"cap4\", \"cap5\"]\n"
        "- Each caption must be unique in angle and tone.\n"
        "- Captions should feel authentic, not generic or clichéd.\n"
        "- No hashtags. No emojis unless they fit naturally.\n"
        "- Keep each caption under 150 characters.\n"
    )

    if style_context:
        base += (
            "\n\nHere are samples of the user's own writing. "
            "Study the voice, rhythm, word choices, and personality — "
            "then mirror that style closely in every caption:\n\n"
            f"{style_context}"
        )
    else:
        base += (
            "\n\nNo writing samples are available yet. "
            "Write in a sharp, thoughtful, modern voice."
        )

    return base


def generate_captions(
    image_bytes: bytes,
    media_type: str,
    style_context: str,
) -> List[str]:
    """
    Send the image + style context to Claude and return 5 captions.

    Args:
        image_bytes: Raw image bytes.
        media_type: MIME type, e.g. "image/jpeg".
        style_context: Concatenated writing samples for style priming.

    Returns:
        List of 5 caption strings.
    """
    import json

    client = get_client()
    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
    system_prompt = _build_system_prompt(style_context)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Generate 5 captions for this photo in my writing style. "
                            "Return only a JSON array of 5 strings."
                        ),
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    captions: List[str] = json.loads(raw)

    if not isinstance(captions, list) or len(captions) != 5:
        raise ValueError(f"Unexpected response format from Claude: {raw}")

    return [str(c).strip() for c in captions]
