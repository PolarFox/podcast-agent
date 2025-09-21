from __future__ import annotations

import logging
import time
from typing import Iterable, List

from .fetchers import fetch_rss_entries, fetch_http_entries
from .models import Article, Source
from .processors import (
    Deduplicator,
    clean_html_to_text,
    classify_text,
    summarize_text,
)
from .processors.impact import generate_impact_points
from .output.issue_formatter import format_issue_title, format_issue_body, labels_for_article
from .output.github_client import GitHubClient

logger = logging.getLogger("ja.orchestrator")


class Orchestrator:
    def __init__(
        self,
        *,
        dry_run: bool = False,
        max_items_per_source: int | None = None,
        max_total_items: int | None = None,
    ) -> None:
        self.dry_run = dry_run
        self.max_items_per_source = max_items_per_source
        self.max_total_items = max_total_items
        self.dedup = Deduplicator()

    def _fetch_source(self, source: Source) -> List[Article]:
        articles: List[Article] = []
        try:
            if source.type == "rss":
                for item in fetch_rss_entries(source):
                    raw_text = item.content or item.description or ""
                    articles.append(
                        Article(
                            title=item.title,
                            url=item.link,
                            source=source.name,
                            raw_text=raw_text,
                            published_date=item.published.isoformat() if item.published else None,
                        )
                    )
            elif source.type == "http":
                for item in fetch_http_entries(source):
                    articles.append(
                        Article(
                            title=item.title or source.name,
                            url=item.url,
                            source=source.name,
                            raw_text=item.content or item.description or "",
                        )
                    )
            else:
                logger.warning("Unknown source type: %s", source.type)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch from %s: %s", source.name, exc)
        return articles

    def run(self, sources: Iterable[Source]) -> None:
        prior_titles: List[str] = []
        gh = GitHubClient(dry_run=self.dry_run)

        fetched_count = 0
        created_issues = 0
        duplicates = 0
        classify_ms = 0.0
        summarize_ms = 0.0
        bullets_ms = 0.0

        processed_non_duplicate = 0
        for src in sources:
            fetched = self._fetch_source(src)
            fetched_count += len(fetched)

            # Limit items per source for quick/CI runs
            if self.max_items_per_source is not None and self.max_items_per_source >= 0:
                fetched = fetched[: self.max_items_per_source]

            for art in fetched:
                # Normalize
                art.raw_text = clean_html_to_text(art.raw_text)

                # Deduplicate
                is_dup, reason = self.dedup.is_duplicate(art, prior_titles=prior_titles)
                if is_dup:
                    duplicates += 1
                    logger.info("Skipping duplicate (%s): %s", reason, art.title)
                    continue
                self.dedup.mark_seen(art)
                prior_titles.append(art.title)

                # Classify
                t0 = time.perf_counter()
                category, conf = classify_text(art.raw_text)
                classify_ms += (time.perf_counter() - t0) * 1000
                logger.debug("Classified '%s' as %s (%.2f)", art.title, category, conf)
                art.category = category
                art.confidence_score = conf

                # Summarize
                t0 = time.perf_counter()
                art.summary = summarize_text(art.raw_text)
                summarize_ms += (time.perf_counter() - t0) * 1000

                # Impact points
                t0 = time.perf_counter()
                impact_points = generate_impact_points(art.raw_text)
                bullets_ms += (time.perf_counter() - t0) * 1000

                # Format + create issue
                title = format_issue_title(art)
                body = format_issue_body(art, impact_points=impact_points)
                labels = labels_for_article(art)
                gh.create_issue(title=title, body=body, labels=labels)
                created_issues += 1
                processed_non_duplicate += 1

                if (
                    self.max_total_items is not None
                    and self.max_total_items >= 0
                    and processed_non_duplicate >= self.max_total_items
                ):
                    logger.info(
                        "Reached max_total_items=%s; stopping early",
                        self.max_total_items,
                    )
                    break

            if (
                self.max_total_items is not None
                and self.max_total_items >= 0
                and processed_non_duplicate >= self.max_total_items
            ):
                break

        logger.info(
            "Pipeline finished: fetched=%s, duplicates=%s, created_issues=%s, classify_ms=%.1f, summarize_ms=%.1f, bullets_ms=%.1f",
            fetched_count,
            duplicates,
            created_issues,
            classify_ms,
            summarize_ms,
            bullets_ms,
        )
