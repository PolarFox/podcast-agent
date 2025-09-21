"""Application entrypoint for the Johtava Arkkitehti Podcast agent.

This script orchestrates the high-level flow:
1) load configuration
2) fetch/process content
3) create GitHub issues (or dry-run)
"""

from __future__ import annotations

import argparse
import os
import logging
from pathlib import Path

from .utils.logging import configure_logging, get_logger
from .utils.config_loader import load_sources_config
from .orchestrator import Orchestrator
from .analysis import (
    prioritize_articles,
    write_monthly_analysis_file,
    build_monthly_summary,
    write_monthly_data_to_repo,
)
from .pipeline.issue_pipeline import run_auto_issue_pipeline
from .utils.pipeline_config import PipelineConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Johtava Arkkitehti Podcast agent – fetch, process, and draft topics"
        )
    )
    parser.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to sources configuration file (YAML)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without contacting external services; print planned actions",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Only generate monthly situational analysis and exit",
    )
    parser.add_argument(
        "--monthly-data-only",
        action="store_true",
        help="Only generate monthly data JSON and exit (commit with --commit-monthly-data)",
    )
    parser.add_argument(
        "--commit-monthly-data",
        action="store_true",
        help="Commit generated monthly data JSON to the target repository from env",
    )
    parser.add_argument(
        "--auto-issues",
        action="store_true",
        help="Analyze, group, and automatically create grouped GitHub issues",
    )
    parser.add_argument(
        "--horizon-weeks",
        type=int,
        default=4,
        help="Planning horizon in weeks for monthly analysis",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--max-items-per-source",
        type=int,
        default=None,
        help="Limit number of items processed per source (for quick dry-runs)",
    )
    parser.add_argument(
        "--max-total-items",
        type=int,
        default=None,
        help="Stop after processing this many non-duplicate items (for quick runs)",
    )
    return parser.parse_args()


def main() -> int:
    # Optional: load .env
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(override=False)
    except Exception:
        pass
    args = parse_args()
    configure_logging(level=args.log_level)
    logger = get_logger("ja.agent")

    config_path = Path(args.config)
    logger.info("Loading sources configuration from %s", config_path)
    try:
        sources = load_sources_config(config_path)
    except Exception as exc:  # noqa: BLE001 - top-level entrypoint guard
        logger.exception("Failed to load configuration: %s", exc)
        return 1

    logger.info("Loaded %d source(s)", len(sources))

    if args.analysis_only:
        # Lightweight fetch-only to build candidate list for prioritization
        orch = Orchestrator(
            dry_run=True,
            max_items_per_source=args.max_items_per_source,
            max_total_items=args.max_total_items,
        )
        prior_arts = []
        for src in sources:
            prior_arts.extend(orch._fetch_source(src))  # intentionally reuse fetch
        items = prioritize_articles(prior_arts, horizon_weeks=args.horizon_weeks)
        path = write_monthly_analysis_file(items, horizon_weeks=args.horizon_weeks)
        logger.info("Wrote monthly analysis to %s", path)
        return 0

    if args.monthly_data_only:
        # Build processed articles quickly
        orch = Orchestrator(
            dry_run=True,
            max_items_per_source=args.max_items_per_source,
            max_total_items=args.max_total_items,
        )
        prior_arts = []
        for src in sources:
            prior_arts.extend(orch._fetch_source(src))
        summary = build_monthly_summary(prior_arts, horizon_weeks=args.horizon_weeks)
        if args.commit_monthly_data and not args.dry_run:
            path_repo = write_monthly_data_to_repo(summary)
            logger.info("Committed monthly data to %s", path_repo)
        else:
            out_dir = Path("docs/monthly")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"summaries-{summary.month}.json"
            out_path.write_text(summary.to_json_str(), encoding="utf-8")
            logger.info("Wrote monthly data JSON to %s (not committed)", out_path)
        return 0

    if args.auto_issues:
        # Fetch only to build candidate list; do not create per-article issues here
        orch = Orchestrator(
            dry_run=True,
            max_items_per_source=args.max_items_per_source,
            max_total_items=args.max_total_items,
        )
        candidates = []
        for src in sources:
            candidates.extend(orch._fetch_source(src))
        cfg = PipelineConfig()
        results = run_auto_issue_pipeline(
            candidates,
            horizon_weeks=cfg.horizon_weeks,
            min_score=cfg.min_score,
            group_max_items=cfg.group_max_items,
            default_assignees=cfg.default_assignees,
            dry_run=args.dry_run,
        )
        logger.info("Auto-issues created: %s", [r for r in results if r is not None])
        return 0

    orch = Orchestrator(
        dry_run=args.dry_run,
        max_items_per_source=args.max_items_per_source,
        max_total_items=args.max_total_items,
    )
    orch.run(sources)
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
