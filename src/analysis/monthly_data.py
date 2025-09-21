from __future__ import annotations

import calendar
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from github import Github, GithubException

from ..models import Article, Source
from ..fetchers import fetch_http_entries, fetch_rss_entries
from ..processors import (
    Deduplicator,
    clean_html_to_text,
    classify_text,
    summarize_text,
)
from .prioritize import PrioritizedItem, prioritize_articles
from ..utils.logging import get_logger

logger = get_logger("ja.analysis.monthly")


@dataclass(slots=True)
class MonthlyItem:
    title: str
    url: str
    source: str
    published_date: Optional[str]
    category: Optional[str]
    summary: Optional[str]
    score: Optional[float]


@dataclass(slots=True)
class MonthlySummary:
    month: str  # YYYY-MM
    generated_at: str
    items: List[MonthlyItem]
    category_counts: Dict[str, int]
    top_keywords: List[Tuple[str, int]]

    def to_json_str(self) -> str:
        payload = {
            "month": self.month,
            "generated_at": self.generated_at,
            "items": [asdict(i) for i in self.items],
            "category_counts": self.category_counts,
            "top_keywords": self.top_keywords,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


def _month_slug(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def previous_month_slug(now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    year = now.year
    month = now.month - 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def _extract_keywords(title: str) -> List[str]:
    words = [w.strip(".,:;!?()[]\"'") for w in (title or "").lower().split()]
    return [w for w in words if len(w) >= 4]


def _compute_category_counts(items: List[MonthlyItem]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for it in items:
        cat = it.category or "Uncategorized"
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _compute_top_keywords(items: List[MonthlyItem], *, top_k: int = 15) -> List[Tuple[str, int]]:
    freq: Dict[str, int] = {}
    for it in items:
        for k in _extract_keywords(it.title):
            freq[k] = freq.get(k, 0) + 1
    return sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]


def collect_processed_articles(sources: Iterable[Source], *, fast: bool = False) -> List[Article]:
    dedup = Deduplicator()
    prior_titles: List[str] = []
    processed: List[Article] = []

    for src in sources:
        try:
            fetched: List[Article] = []
            if src.type == "rss":
                for item in fetch_rss_entries(src):
                    raw_text = item.content or item.description or ""
                    fetched.append(
                        Article(
                            title=item.title,
                            url=item.link,
                            source=src.name,
                            raw_text=raw_text,
                            published_date=item.published.isoformat() if item.published else None,
                        )
                    )
            elif src.type == "http":
                for item in fetch_http_entries(src):
                    fetched.append(
                        Article(
                            title=item.title or src.name,
                            url=item.url,
                            source=src.name,
                            raw_text=item.content or item.description or "",
                        )
                    )
            else:
                logger.warning("Unknown source type: %s", src.type)
                continue

            for art in fetched:
                # Normalize
                art.raw_text = clean_html_to_text(art.raw_text)

                # Dedup
                is_dup, _ = dedup.is_duplicate(art, prior_titles=prior_titles)
                if is_dup:
                    continue
                dedup.mark_seen(art)
                prior_titles.append(art.title)

                # Classify
                if fast:
                    art.category = art.category or "Architecture/Infra"
                    art.confidence_score = 0.0
                else:
                    try:
                        category, conf = classify_text(art.raw_text)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Classification failed: %s; defaulting", exc)
                        category, conf = "Architecture/Infra", 0.0
                    art.category = category
                    art.confidence_score = conf

                # Summarize
                if fast:
                    words = art.raw_text.split()
                    art.summary = " ".join(words[:60]) + ("..." if len(words) > 60 else "")
                else:
                    try:
                        art.summary = summarize_text(art.raw_text)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Summarization failed: %s; pending", exc)
                        art.summary = "(summary pending)"

                processed.append(art)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed processing source %s: %s", src.name, exc)
    return processed


def build_monthly_summary(articles: Iterable[Article], *, horizon_weeks: int = 4, top_n: int = 200) -> MonthlySummary:
    items_scored: List[PrioritizedItem] = prioritize_articles(articles, horizon_weeks=horizon_weeks, top_n=top_n)
    items = [
        MonthlyItem(
            title=it.article.title,
            url=it.article.url,
            source=it.article.source,
            published_date=it.article.published_date,
            category=it.article.category,
            summary=it.article.summary,
            score=it.score,
        )
        for it in items_scored
    ]
    cat_counts = _compute_category_counts(items)
    top_keywords = _compute_top_keywords(items)

    now = datetime.now(timezone.utc)
    month = _month_slug(now)
    return MonthlySummary(
        month=month,
        generated_at=now.isoformat(),
        items=items,
        category_counts=cat_counts,
        top_keywords=top_keywords,
    )


def write_monthly_data_to_repo(
    summary: MonthlySummary,
    *,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    token: Optional[str] = None,
    path_prefix: str = "data/monthly",
) -> str:
    """Create or update the monthly data JSON in the target repo.

    Returns the path committed in the repository.
    """
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_KEY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN/GITHUB_API_KEY is required to commit monthly data")

    # Repo resolution: explicit -> MONTHLY_DATA_REPOSITORY -> DATA_REPOSITORY -> GITHUB_REPOSITORY
    repo_name = (
        repo_name
        or os.environ.get("MONTHLY_DATA_REPOSITORY")
        or os.environ.get("DATA_REPOSITORY")
        or os.environ.get("GITHUB_REPOSITORY")
    )
    if not repo_name:
        raise RuntimeError("Target repository is not configured (MONTHLY_DATA_REPOSITORY/DATA_REPOSITORY/GITHUB_REPOSITORY)")

    gh = Github(token)
    repo = gh.get_repo(repo_name)
    if branch is None:
        try:
            branch = repo.default_branch or "main"
        except Exception:
            branch = "main"

    filename = f"summaries-{summary.month}.json"
    repo_path = f"{path_prefix.rstrip('/')}/{filename}"
    content_str = summary.to_json_str()
    message = f"chore(data): update monthly summaries for {summary.month}"

    try:
        existing = repo.get_contents(repo_path, ref=branch)
        repo.update_file(repo_path, message, content_str, existing.sha, branch=branch)
        logger.info("Updated monthly data file at %s@%s", repo_path, branch)
    except GithubException as exc:
        status = getattr(exc, "status", None)
        if status == 404:
            repo.create_file(repo_path, message, content_str, branch=branch)
            logger.info("Created monthly data file at %s@%s", repo_path, branch)
        else:
            logger.error("GitHub API error writing data file: %s", exc)
            raise

    return repo_path


def monthly_data_exists(
    *,
    month_slug: Optional[str] = None,
    repo_name: Optional[str] = None,
    branch: Optional[str] = None,
    token: Optional[str] = None,
    path_prefix: str = "data/monthly",
) -> bool:
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_KEY")
    if not token:
        # Without auth we cannot reliably check private repos; treat as missing
        logger.info("No GitHub token; skipping monthly data existence check (treating as missing)")
        return False

    repo_name = (
        repo_name
        or os.environ.get("MONTHLY_DATA_REPOSITORY")
        or os.environ.get("DATA_REPOSITORY")
        or os.environ.get("GITHUB_REPOSITORY")
    )
    if not repo_name:
        logger.warning("No target repository configured for monthly data existence check")
        return False

    gh = Github(token)
    repo = gh.get_repo(repo_name)
    if branch is None:
        try:
            branch = repo.default_branch or "main"
        except Exception:
            branch = "main"

    if month_slug is None:
        month_slug = _month_slug(datetime.now(timezone.utc))
    filename = f"summaries-{month_slug}.json"
    repo_path = f"{path_prefix.rstrip('/')}/{filename}"
    try:
        repo.get_contents(repo_path, ref=branch)
        return True
    except GithubException as exc:
        status = getattr(exc, "status", None)
        if status == 404:
            return False
        raise
