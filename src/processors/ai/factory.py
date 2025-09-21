from __future__ import annotations

import os
from typing import Optional

from .base import AIClient


def create_ai_client(*, backend: Optional[str] = None) -> AIClient:
    """Create an AI client based on PROCESSING_BACKEND env or explicit value.

    Supported values: "ollama" (default) or "gemini". No local fallbacks.
    """
    selected = (backend or os.environ.get("PROCESSING_BACKEND", "ollama")).lower()

    if selected == "ollama":
        from .ollama import OllamaClient  # lazy import

        return OllamaClient()
    if selected == "gemini":
        from .gemini import GeminiClient  # lazy import

        return GeminiClient()

    raise ValueError(
        f"Unsupported PROCESSING_BACKEND '{selected}'. Use 'ollama' or 'gemini'."
    )
