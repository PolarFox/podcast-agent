from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple


class AIClient(ABC):
    """Abstract AI client interface for classification and summarization."""

    @abstractmethod
    def classify(self, text: str) -> Tuple[str, float]:
        """Return (category, confidence) for the given text."""

    @abstractmethod
    def summarize(self, text: str, *, max_words: int = 150) -> str:
        """Return a concise summary of the text."""
