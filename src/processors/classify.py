from __future__ import annotations

import json
import logging
from typing import Tuple

from .ai import AIClient, create_ai_client

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

    category, conf = ai.classify(text)
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
