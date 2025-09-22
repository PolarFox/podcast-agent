from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from ..models import Article
from .prioritize import PrioritizedItem, prioritize_articles
from .quota_redistributor import redistribute_shortfalls

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


def score_and_bucket(
    articles: Iterable[Article], *, horizon_weeks: int = 4, top_n: int = 2000
) -> Dict[str, List[PrioritizedItem]]:
    scored: List[PrioritizedItem] = prioritize_articles(articles, horizon_weeks=horizon_weeks, top_n=top_n)
    buckets: Dict[str, List[PrioritizedItem]] = defaultdict(list)
    for it in scored:
        cat = it.article.category or "Uncategorized"
        buckets[cat].append(it)
    return buckets


def select_with_redistribution(
    articles: Iterable[Article], *, per_category: int = 16, total: int = 64, horizon_weeks: int = 4
) -> Dict[str, List[PrioritizedItem]]:
    buckets = score_and_bucket(articles, horizon_weeks=horizon_weeks)
    selected: Dict[str, List[PrioritizedItem]] = {c: [] for c in CATEGORIES}
    for cat in CATEGORIES:
        pool = buckets.get(cat, [])
        selected[cat] = pool[:per_category]
    final = redistribute_shortfalls(buckets=buckets, selected=selected, target_total=total, per_category_limit=per_category)
    return final
