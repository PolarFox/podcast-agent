from __future__ import annotations

import json
import logging
from typing import Tuple

from .ai import AIClient, create_ai_client
from .ai.retry import classify_with_retry

logger = logging.getLogger("ja.processors.classify")

_CATEGORIES = ["Agile", "DevOps", "Architecture/Infra", "Leadership"]


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
