from __future__ import annotations

from typing import Iterable, List

from ..models import Article
from .prioritize import PrioritizedItem, prioritize_articles


class ArticlePrioritizer:
    def __init__(self, *, horizon_weeks: int = 4) -> None:
        self.horizon_weeks = horizon_weeks

    def score(self, articles: Iterable[Article], *, top_n: int = 2000) -> List[PrioritizedItem]:
        return prioritize_articles(articles, horizon_weeks=self.horizon_weeks, top_n=top_n)
