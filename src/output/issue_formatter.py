from __future__ import annotations

from typing import List

from ..models import Article

_CATEGORY_TO_LABEL = {
    "Agile": "agile",
    "DevOps": "devops",
    "Architecture/Infra": "architecture",
    "Leadership": "leadership",
}


def labels_for_article(article: Article) -> List[str]:
    return ["draft", _CATEGORY_TO_LABEL.get(article.category or "", "uncategorized")]


def format_issue_title(article: Article) -> str:
    cat = article.category or "Uncategorized"
    return f"[{cat}] {article.title}"


def format_issue_body(article: Article, impact_points: List[str] | None = None) -> str:
    impact_points = impact_points or []
    labels = labels_for_article(article)

    points_md = "\n".join(f"- {p}" for p in impact_points)
    summary = article.summary or "(summary pending)"

    return (
        f"### Summary\n\n{summary}\n\n"
        f"### Impact to teams\n\n{points_md if points_md else '- TBD'}\n\n"
        f"### Original Source\n\n{article.url}\n\n"
        f"---\nLabels: {', '.join(labels)}\n"
    )
