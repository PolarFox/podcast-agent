from __future__ import annotations

import os
import time
import time
from typing import List, Optional

from github import Github, GithubException

from ..utils.logging import get_logger

logger = get_logger("ja.output.github")


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
        try:
            rl = self._client.get_rate_limit()
            remaining = None
            reset_ts = None

            # PyGithub classic style
            core = getattr(rl, "core", None)
            if core is not None:
                remaining = getattr(core, "remaining", None)
                reset = getattr(core, "reset", None)
                if hasattr(reset, "timestamp"):
                    reset_ts = reset.timestamp()

            # Newer overview style (.resources) or dict-like
            if remaining is None:
                resources = getattr(rl, "resources", None)
                core_res = None
                if resources is not None:
                    core_res = getattr(resources, "core", None)
                    if core_res is None and isinstance(resources, dict):
                        core_res = resources.get("core")
                if core_res is not None:
                    remaining = getattr(core_res, "remaining", None) if not isinstance(core_res, dict) else core_res.get("remaining")
                    reset = getattr(core_res, "reset", None) if not isinstance(core_res, dict) else core_res.get("reset")
                    if hasattr(reset, "timestamp"):
                        reset_ts = reset.timestamp()

            if remaining is not None and reset_ts is not None and remaining <= 1:
                sleep_s = max(0, reset_ts - time.time())
                logger.info("GitHub rate limit reached; sleeping %.1fs until reset", sleep_s)
                time.sleep(sleep_s)
        except Exception as exc:  # noqa: BLE001
            # If the shape changes or unauthenticated, skip sleeping and try the call
            logger.debug("Skipping rate limit sleep due to error: %s", exc)

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
