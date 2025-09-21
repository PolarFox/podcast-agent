from __future__ import annotations

import time
import os
from typing import Callable, TypeVar

from .base import AIClient
from ...utils.logging import get_logger

T = TypeVar("T")
logger = get_logger("ja.ai.retry")


def with_retries(fn: Callable[[], T], *, retries: int = 2, backoff: float = 1.5) -> T:
    # Environment overrides for quick runs: AI_RETRIES, AI_BACKOFF
    try:
        env_retries = os.getenv("AI_RETRIES")
        if env_retries is not None:
            retries = int(env_retries)
    except Exception:  # noqa: BLE001 - ignore invalid env
        pass
    try:
        env_backoff = os.getenv("AI_BACKOFF")
        if env_backoff is not None:
            backoff = float(env_backoff)
    except Exception:  # noqa: BLE001 - ignore invalid env
        pass
    last_exc: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= retries:
                break
            sleep_s = backoff ** attempt
            logger.warning("AI call failed (attempt %s/%s): %s; retrying in %.1fs", attempt + 1, retries + 1, exc, sleep_s)
            time.sleep(sleep_s)
    assert last_exc is not None
    raise last_exc


def classify_with_retry(client: AIClient, text: str):
    return with_retries(lambda: client.classify(text))


def summarize_with_retry(client: AIClient, text: str, *, max_words: int = 150):
    return with_retries(lambda: client.summarize(text, max_words=max_words))
