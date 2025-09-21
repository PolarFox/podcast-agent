from __future__ import annotations

from typing import Iterable, List, Sequence

from ..models import Article
from ..analysis.priority_analyzer import filter_high_priority
from ..analysis.article_grouper import group_related_articles
from ..analysis.duplicate_tracker import DuplicateTracker
from ..output.issue_formatter import (
    format_group_issue_title,
    format_group_issue_body,
    labels_for_article,
)
from ..output.github_client import GitHubClient
from ..utils.logging import get_logger


logger = get_logger("ja.pipeline.issues")


def run_auto_issue_pipeline(
    articles: Iterable[Article],
    *,
    horizon_weeks: int = 4,
    min_score: float = 0.7,
    group_max_items: int = 4,
    dry_run: bool = False,
) -> List[int | None]:
    """Create grouped GitHub issues from high-priority articles.

    Returns a list of created issue numbers (or None in dry-run).
    """
    prioritized = filter_high_priority(articles, horizon_weeks=horizon_weeks, min_score=min_score)
    high_priority_articles: List[Article] = [it.article for it in prioritized]

    groups = group_related_articles(high_priority_articles, max_per_group=group_max_items)
    if not groups:
        logger.info("No candidate groups for issue creation")
        return []

    dup = DuplicateTracker()
    gh = GitHubClient(dry_run=dry_run)

    payloads = []
    for grp in groups:
        if dup.has_seen_articles(grp):
            logger.info("Skipping duplicate group with first title: %s", grp[0].title)
            continue
        title = format_group_issue_title(grp)
        body = format_group_issue_body(grp)
        # label by the first article's category
        labels = labels_for_article(grp[0])
        payloads.append({"title": title, "body": body, "labels": labels})

    results = gh.create_issues_batch(payloads, delay_seconds=1.0)

    # Record created ones
    for grp, num in zip(groups, results):
        if num is not None:
            dup.record_issue(title=grp[0].title, articles=grp, issue_number=num)

    return results
