from __future__ import annotations

from typing import Dict, List

from .prioritize import PrioritizedItem
from .category_selector import CATEGORIES


def redistribute_shortfalls(
    *,
    buckets: Dict[str, List[PrioritizedItem]],
    selected: Dict[str, List[PrioritizedItem]],
    target_total: int = 64,
    per_category_limit: int = 16,
) -> Dict[str, List[PrioritizedItem]]:
    result = {c: list(selected.get(c, [])) for c in CATEGORIES}
    current_total = sum(len(v) for v in result.values())
    if current_total >= target_total:
        return result

    # Build a global tail pool preserving overall score order
    global_tail: List[PrioritizedItem] = []
    for cat in CATEGORIES:
        pool = buckets.get(cat, [])
        already = set(id(x) for x in result.get(cat, []))
        for it in pool:
            if id(it) not in already:
                global_tail.append(it)

    # Sort tail by score desc then title asc to ensure determinism
    global_tail.sort(key=lambda it: (it.score, it.article.title.lower()), reverse=True)

    # Fill remaining slots while respecting per-category caps
    needed = target_total - current_total
    for it in global_tail:
        if needed <= 0:
            break
        cat = it.article.category or "Uncategorized"
        if cat not in result:
            continue
        if len(result[cat]) >= per_category_limit:
            continue
        result[cat].append(it)
        needed -= 1

    return result
