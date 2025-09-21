"""Application entrypoint for the Johtava Arkkitehti Podcast agent.

This script orchestrates the high-level flow:
1) load configuration
2) fetch/process content
3) create GitHub issues (or dry-run)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .utils.logging import configure_logging
from .utils.config_loader import load_sources_config
from .orchestrator import Orchestrator
from .analysis import prioritize_articles, write_monthly_analysis_file


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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(level=args.log_level)
    logger = logging.getLogger("ja.agent")

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
        orch = Orchestrator(dry_run=True)
        prior_arts = []
        for src in sources:
            prior_arts.extend(orch._fetch_source(src))  # intentionally reuse fetch
        items = prioritize_articles(prior_arts, horizon_weeks=args.horizon_weeks)
        path = write_monthly_analysis_file(items, horizon_weeks=args.horizon_weeks)
        logger.info("Wrote monthly analysis to %s", path)
        return 0

    orch = Orchestrator(dry_run=args.dry_run)
    orch.run(sources)
    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
