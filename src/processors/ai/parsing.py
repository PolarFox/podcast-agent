from __future__ import annotations

import json
import re
from typing import Tuple

_ALLOWED_CATEGORIES = {"Agile", "DevOps", "Architecture/Infra", "Leadership"}


def parse_classification_response(raw: str) -> Tuple[str, float]:
    """Parse and validate AI classification JSON.

    Expected object with keys:
      - category: one of _ALLOWED_CATEGORIES
      - confidence: float in [0, 1]
    """
    if not raw or not raw.strip():
        raise ValueError("Empty AI response")

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("No JSON object found in AI response")

    obj = json.loads(match.group(0))

    category_val = obj.get("category", "")
    if not isinstance(category_val, str):
        raise ValueError("'category' must be a string")
    category = category_val.strip()
    if category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'")

    confidence_val = obj.get("confidence", None)
    try:
        confidence = float(confidence_val)
    except Exception as exc:
        raise ValueError(f"Invalid confidence '{confidence_val}': {exc}")

    if not (0.0 <= confidence <= 1.0):
        raise ValueError(f"Confidence out of range: {confidence}")

    return category, confidence
