from __future__ import annotations

import logging
import os
import time
from typing import List, Optional

from github import Github, GithubException

logger = logging.getLogger("ja.output.github")


class GitHubClient:
    def __init__(self, *, token: Optional[str] = None, repo: Optional[str] = None, dry_run: bool = False) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_KEY")
        if not self.token and not dry_run:
            raise RuntimeError("GITHUB_TOKEN/GITHUB_API_KEY not set and dry_run=False")
        self.repo_name = repo or os.environ.get("GITHUB_REPOSITORY")
        self.dry_run = dry_run
        self._client = Github(self.token) if self.token else None
        self._repo = None
        if self._client and self.repo_name:
            self._repo = self._client.get_repo(self.repo_name)

    def _rate_limit_sleep(self) -> None:
        if not self._client:
            return
        core = self._client.get_rate_limit().core
        if core.remaining <= 1:
            reset_ts = core.reset.timestamp()
            sleep_s = max(0, reset_ts - time.time())
            logger.info("GitHub rate limit reached; sleeping %.1fs until reset", sleep_s)
            time.sleep(sleep_s)

    def create_issue(self, *, title: str, body: str, labels: List[str] | None = None) -> Optional[int]:
        labels = labels or ["draft"]
        if self.dry_run:
            logger.info("[DRY-RUN] Would create issue: title=%s labels=%s", title, labels)
            return None

        if not self._repo:
            if not self.repo_name:
                raise RuntimeError("Repository not provided (env GITHUB_REPOSITORY)")
            self._repo = self._client.get_repo(self.repo_name)

        backoff = 1.5
        for attempt in range(4):
            try:
                self._rate_limit_sleep()
                issue = self._repo.create_issue(title=title, body=body, labels=labels)
                logger.info("Created GitHub issue #%s", issue.number)
                return issue.number
            except GithubException as exc:
                status = getattr(exc, "status", None)
                if status in (403, 429):
                    # rate limited or forbidden; try after delay
                    delay = backoff ** attempt
                    logger.warning("GitHub API throttled/forbidden (%s). Retrying in %.1fs", status, delay)
                    time.sleep(delay)
                    continue
                if status in (422, 404):
                    logger.error("GitHub API error %s: %s", status, exc)
                    raise
                logger.warning("GitHub exception: %s; retrying", exc)
                time.sleep(backoff ** attempt)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unexpected error creating issue: %s; retrying", exc)
                time.sleep(backoff ** attempt)
        raise RuntimeError("Failed to create issue after retries")
