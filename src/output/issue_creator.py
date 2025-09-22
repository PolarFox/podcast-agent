from __future__ import annotations

from typing import Iterable, Optional, Sequence

from ..models import Article
from .github_client import GitHubClient
from .issue_formatter import (
    labels_for_article,
    format_issue_title,
    format_issue_body,
    format_group_issue_title,
    format_group_issue_body,
)
from ..utils.logging import get_logger


logger = get_logger("ja.output.issue_creator")


class GitHubIssueCreator:
    def __init__(self, *, token: Optional[str] = None, repo: Optional[str] = None, dry_run: bool = False) -> None:
        self.client = GitHubClient(token=token, repo=repo, dry_run=dry_run)

    def create_issue_from_article(self, article: Article, *, assignees: Optional[Sequence[str]] = None) -> Optional[int]:
        title = format_issue_title(article)
        body = format_issue_body(article)
        labels = labels_for_article(article)
        return self.client.create_issue(title=title, body=body, labels=labels, assignees=assignees)

    def create_issue_from_group(
        self,
        articles: Sequence[Article],
        *,
        impact_points: Sequence[str] | None = None,
        assignees: Optional[Sequence[str]] = None,
    ) -> Optional[int]:
        if not articles:
            logger.info("No articles provided for grouped issue")
            return None
        title = format_group_issue_title(articles)
        body = format_group_issue_body(articles, impact_points=impact_points)
        # Use first article's category for labels
        labels = labels_for_article(articles[0])
        return self.client.create_issue(title=title, body=body, labels=labels, assignees=assignees)
