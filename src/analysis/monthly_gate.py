from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .monthly_data import monthly_data_exists
from ..utils.logging import get_logger


logger = get_logger("ja.analysis.monthly_gate")


@dataclass(slots=True)
class MonthlyGateStatus:
    month_slug: str
    exists: bool


def _current_month_slug() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def is_monthly_ready(month_slug: Optional[str] = None) -> MonthlyGateStatus:
    slug = month_slug or _current_month_slug()
    exists = monthly_data_exists(month_slug=slug)
    return MonthlyGateStatus(month_slug=slug, exists=exists)


def ensure_monthly_ready(month_slug: Optional[str] = None) -> None:
    status = is_monthly_ready(month_slug)
    if not status.exists:
        logger.info(
            "Monthly data missing for %s. Generate it with --monthly-data-only --commit-monthly-data",
            status.month_slug,
        )
        raise RuntimeError(
            f"Monthly data not found for {status.month_slug}. Please run --monthly-data-only --commit-monthly-data first."
        )
