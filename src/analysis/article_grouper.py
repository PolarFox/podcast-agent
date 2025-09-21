from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

from ..models import Article

Group = List[Article]


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _category_key(article: Article) -> str:
    return (article.category or "Uncategorized").strip()


def _keyword_signature(title: str, *, min_len: int = 4) -> Tuple[str, ...]:
    words = [w.strip(".,:;!?") for w in (title or "").split()]
    keywords = [w.lower() for w in words if len(w) >= min_len]
    # dedupe while preserving order
    seen = set()
    sig: List[str] = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            sig.append(w)
    return tuple(sig)


def group_related_articles(
    articles: Iterable[Article], *, max_per_group: int = 4
) -> List[Group]:
    """Naive grouping by (category, keyword signature prefix).

    This is a fast, deterministic heuristic suitable as a first version.
    """
    buckets: Dict[Tuple[str, Tuple[str, ...]], List[Article]] = defaultdict(list)
    for art in articles:
        cat = _category_key(art)
        sig = _keyword_signature(art.title)
        key = (cat, sig[:3])  # first 3 keywords define the topic bucket
        buckets[key].append(art)

    groups: List[Group] = []
    for (_cat, _sig), items in buckets.items():
        # enforce max size per group to keep issues readable
        chunk: Group = []
        for art in items:
            chunk.append(art)
            if len(chunk) >= max_per_group:
                groups.append(chunk)
                chunk = []
        if chunk:
            groups.append(chunk)
    # Sort groups by size desc, then by first title for determinism
    groups.sort(key=lambda g: (-len(g), _norm(g[0].title)))
    return groups
