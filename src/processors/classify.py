from __future__ import annotations

import json
from typing import Tuple

import os

from .ai import AIClient, create_ai_client
from .ai.retry import classify_with_retry
from ..utils.logging import get_logger

logger = get_logger("ja.processors.classify")

_CATEGORIES = ["Agile", "DevOps", "Architecture/Infra", "Leadership"]


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]) if len(words) > max_words else text


def classify_text(
    text: str,
    *,
    ai: AIClient | None = None,
) -> Tuple[str, float]:
    """Classify text strictly via configured AI backend.

    Returns (category, confidence)
    """
    if ai is None:
        ai = create_ai_client()

    # Guard: extremely short texts are hard to classify reliably; still use AI but expect low confidence
    content = text.strip()
    if len(content.split()) < 8:
        logger.debug("Very short content; classification may be unreliable")

    # Truncate input for faster classification in local runs
    try:
        max_words = int(os.getenv("AI_INPUT_TRUNCATE_WORDS", "600"))
        if max_words > 0:
            content = _truncate_words(content, max_words)
    except Exception:  # noqa: BLE001
        pass

    # Use retry wrapper for resilience against transient backend errors
    category, conf = classify_with_retry(ai, content)
    if category not in _CATEGORIES:
        logger.warning("Invalid category '%s' from AI; defaulting to 'Architecture/Infra'", category)
        return "Architecture/Infra", 0.0
    try:
        conf_f = float(conf)
    except Exception:
        logger.warning("Non-numeric confidence '%s' from AI; coercing to 0.0", conf)
        conf_f = 0.0
    conf_f = max(0.0, min(1.0, conf_f))
    return category, conf_f
