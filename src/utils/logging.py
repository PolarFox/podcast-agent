"""Logging configuration utilities.

Provides a single function to initialize the root logger with a consistent
format suitable for both local development and containerized environments.
"""

from __future__ import annotations

import logging
import os
from typing import Optional


def configure_logging(level: str | int = "INFO", *, module: Optional[str] = None) -> None:
    """Configure application logging.

    Parameters
    ----------
    level:
        Logging level as a string (e.g., "INFO") or numeric value.
    module:
        Optional module name to set a specific logger level for; if not
        provided, config applies to the root logger only.
    """

    # When running in containers, stdout logging is the norm.
    log_level = os.environ.get("LOG_LEVEL", str(level)).upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        ),
    )

    if module is not None:
        logging.getLogger(module).setLevel(getattr(logging, log_level, logging.INFO))
