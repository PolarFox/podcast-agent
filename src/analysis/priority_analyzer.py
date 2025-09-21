from __future__ import annotations

from typing import Iterable, List, Optional

from .prioritize import prioritize_articles, PrioritizedItem
from ..models import Article


def filter_high_priority(
    articles: Iterable[Article],
    *,
    horizon_weeks: int = 4,
    min_score: float = 0.6,
    top_n: Optional[int] = None,
) -> List[PrioritizedItem]:
    """Return prioritized items filtered by minimum score.

    Parameters
    ----------
    articles: Iterable[Article]
        Input articles with at least title, url, source and (optionally) category/summary
    horizon_weeks: int
        Planning horizon to influence recency scoring
    min_score: float
        Minimum overall score threshold to include an item
    top_n: Optional[int]
        Consider at most this many top-ranked items before filtering
    """
    limit = top_n or 1000
    prioritized = prioritize_articles(articles, horizon_weeks=horizon_weeks, top_n=limit)
    return [it for it in prioritized if it.score >= min_score]
