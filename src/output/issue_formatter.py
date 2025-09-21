from __future__ import annotations

from typing import Iterable, List, Sequence

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


def format_group_issue_title(articles: Sequence[Article]) -> str:
    if not articles:
        return "[Draft] Untitled Group"
    primary_cat = articles[0].category or "Uncategorized"
    first_title = articles[0].title
    suffix = "; ".join(a.title for a in articles[1:3])
    tail = f"; {suffix}" if suffix else ""
    return f"[{primary_cat}] Topic roundup: {first_title}{tail}"


def format_group_issue_body(
    articles: Sequence[Article],
    *,
    impact_points: Sequence[str] | None = None,
) -> str:
    """Render a multi-article issue body.

    Sections: Combined Summary, Impact to teams, Sources, Per-article notes.
    """
    impact_points = list(impact_points or [])
    labels = ["draft"]
    # Include primary category label if available
    if articles:
        labels.append(_CATEGORY_TO_LABEL.get(articles[0].category or "", "uncategorized"))

    combined_summary = "\n\n".join(
        f"- {a.summary or '(summary pending)'}" for a in articles
    ) or "(summaries pending)"

    sources_md = "\n".join(f"- [{a.title}]({a.url}) — {a.source}" for a in articles)

    per_article_md = "\n\n".join(
        (
            f"#### {a.title}\n"
            f"Category: {a.category or '-'}\n\n"
            f"Summary:\n\n{a.summary or '(summary pending)'}\n"
        )
        for a in articles
    )

    points_md = "\n".join(f"- {p}" for p in impact_points)

    return (
        f"### Combined Summary\n\n{combined_summary}\n\n"
        f"### Impact to teams\n\n{points_md if points_md else '- TBD'}\n\n"
        f"### Original Sources\n\n{sources_md if sources_md else '-'}\n\n"
        f"### Notes by source\n\n{per_article_md}\n\n"
        f"---\nLabels: {', '.join(labels)}\n"
    )
