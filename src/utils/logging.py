"""Logging configuration utilities.

Provides a single function to initialize the root logger with a consistent
format suitable for both local development and containerized environments.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Literal, Optional

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_OUTPUT = os.environ.get("LOG_OUTPUT", "file").lower()
LOG_FILE_PATH = os.environ.get("LOG_FILE_PATH", "logs/podcast-agent.log")
LOG_FORMAT = os.environ.get("LOG_FORMAT", "text").lower()
K8S_CLUSTER = os.environ.get("K8S_CLUSTER")
KUBERNETES_SERVICE_HOST = os.environ.get("KUBERNETES_SERVICE_HOST")

LogOutput = Literal["stdout", "file", "both"]
LogFormat = Literal["text", "json"]


def is_kubernetes_env() -> bool:
    """Check if the application is running in a Kubernetes environment."""
    return bool(K8S_CLUSTER or KUBERNETES_SERVICE_HOST or os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"))


def configure_logging(
    level: str | int | None = None,
    output: LogOutput | None = None,
    file_path: str | None = None,
    log_format: LogFormat | None = None,
    module: Optional[str] = None,
) -> None:
    """Configure application logging.

    Parameters
    ----------
    level:
        Logging level as a string (e.g., "INFO") or numeric value.
    output:
        Logging output destination: "stdout", "file", or "both".
    file_path:
        Path to the log file if output is "file" or "both".
    log_format:
        Logging format: "text" or "json".
    module:
        Optional module name to set a specific logger level for; if not
        provided, config applies to the root logger only.
    """
    # Resolve effective settings at call-time so .env variables loaded in main() are respected
    if level is None:
        level = os.environ.get("LOG_LEVEL", LOG_LEVEL)
    if log_format is None:
        log_format = (os.environ.get("LOG_FORMAT") or LOG_FORMAT).lower()
    if output is None:
        if is_kubernetes_env() and "LOG_OUTPUT" not in os.environ:
            output = "stdout"
        else:
            output = (os.environ.get("LOG_OUTPUT") or LOG_OUTPUT).lower()
    if file_path is None:
        file_path = os.environ.get("LOG_FILE_PATH") or LOG_FILE_PATH

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = (
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s")
        if log_format == "text"
        else logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "file": "%(filename)s:%(lineno)d", "message": "%(message)s"}')
    )

    if output in ["stdout", "both"]:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        root_logger.addHandler(stdout_handler)

    if output in ["file", "both"]:
        log_dir = os.path.dirname(file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(file_path, maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if module:
        logging.getLogger(module).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
