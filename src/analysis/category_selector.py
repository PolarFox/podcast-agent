from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from ..models import Article
from .prioritize import PrioritizedItem, prioritize_articles

CATEGORIES = ["Agile", "DevOps", "Architecture/Infra", "Leadership"]


def select_top_per_category(
    articles: Iterable[Article], *, per_category: int = 16, horizon_weeks: int = 4
) -> Dict[str, List[PrioritizedItem]]:
    # Score globally then filter per-category for determinism
    scored: List[PrioritizedItem] = prioritize_articles(articles, horizon_weeks=horizon_weeks, top_n=1000)
    buckets: Dict[str, List[PrioritizedItem]] = defaultdict(list)
    for it in scored:
        cat = it.article.category or "Uncategorized"
        buckets[cat].append(it)

    selected: Dict[str, List[PrioritizedItem]] = {c: [] for c in CATEGORIES}
    for cat in CATEGORIES:
        pool = buckets.get(cat, [])
        selected[cat] = pool[:per_category]
    return selected
