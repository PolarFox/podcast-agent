from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal

SourceType = Literal["rss", "http"]


@dataclass(slots=True)
class Source:
    """Configuration for a content source (RSS or HTTP)."""

    name: str
    url: str
    type: SourceType
    keywords: List[str] = field(default_factory=list)
    category_hints: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
