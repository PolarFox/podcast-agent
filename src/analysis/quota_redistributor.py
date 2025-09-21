from __future__ import annotations

from typing import Dict, List

from .prioritize import PrioritizedItem
from .category_selector import CATEGORIES


def redistribute_shortfalls(
    per_category: Dict[str, List[PrioritizedItem]], *, target_total: int = 64
) -> Dict[str, List[PrioritizedItem]]:
    # Compute shortfalls and surplus pools
    result = {c: list(per_category.get(c, [])) for c in CATEGORIES}
    current_total = sum(len(v) for v in result.values())
    if current_total >= target_total:
        return result

    # Build a global surplus pool from any leftover candidates in categories
    # beyond their initial selection (not available here), so we approximate by
    # allowing categories with remaining capacity to take from others' tails.
    # Since we don't have tails, we simply prioritize categories with the most
    # items to fill the remaining slots to reach target.

    remaining = target_total - current_total
    # Greedy: cycle through categories in round-robin, duplicating from their own pool tails as placeholder
    # Note: In a real system, we'd pass scored tails; here we cannot fabricate new items, so we keep counts.
    # Therefore, if we cannot increase total (no extra items), we just return as-is.
    return result
