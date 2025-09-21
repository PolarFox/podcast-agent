from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Article:
    title: str
    url: str
    source: str
    raw_text: str
    published_date: Optional[str] = None

    # AI-derived fields
    category: Optional[str] = None
    summary: Optional[str] = None
    confidence_score: Optional[float] = None
