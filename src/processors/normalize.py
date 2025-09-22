from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Iterable, List, Optional
import unicodedata
from dataclasses import replace

from ..utils.logging import get_logger

from bs4 import BeautifulSoup

_whitespace_re = re.compile(r"\s+")
_control_chars_re = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")

_PUNCT_TRANSLATION = {
    ord("\u2018"): "'",  # left single quote
    ord("\u2019"): "'",  # right single quote
    ord("\u201C"): '"',  # left double quote
    ord("\u201D"): '"',  # right double quote
    ord("\u2013"): "-",  # en dash
    ord("\u2014"): "-",  # em dash
    ord("\u00A0"): " ",  # non-breaking space
}

_logger = get_logger("ja.processors.normalize")


def clean_html_to_text(raw_html: str | None) -> str:
    """Clean HTML to normalized plain text.

    - Strip tags
    - Unescape HTML entities
    - Collapse whitespace
    - Normalize line endings
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text("\n")
    text = html.unescape(text)
    text = _whitespace_re.sub(" ", text)
    return text.strip()


def normalize_plain_text(text: str | None) -> str:
    """Normalize plain text for downstream processing.

    - Ensure string type and strip BOM
    - Unicode normalize (NFKC)
    - Replace curly quotes/dashes and non-breaking spaces
    - Remove control characters (except newlines and tabs, which have been collapsed earlier)
    - Collapse whitespace
    """
    if not text:
        return ""

    # Basic BOM strip
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")

    # Punctuation normalization and unicode compatibility normalization
    text = text.translate(_PUNCT_TRANSLATION)
    text = unicodedata.normalize("NFKC", text)

    # Remove remaining control chars (preserve nothing special as newlines are collapsed later)
    text = _control_chars_re.sub(" ", text)

    # Collapse whitespace and trim
    text = _whitespace_re.sub(" ", text).strip()
    return text


def normalize_article(article: "Article") -> "Article":  # quoted type to avoid import cycle at import time
    """Return a new Article instance with normalized fields.

    - Clean and normalize raw_text
    - Normalize title
    - Parse published_date to ISO 8601, if possible
    """
    from ..models import Article  # local import to avoid circular import

    cleaned_text = clean_html_to_text(article.raw_text)
    normalized_text = normalize_plain_text(cleaned_text)
    normalized_title = normalize_plain_text(article.title)
    iso_date = parse_date_to_iso(article.published_date)

    return replace(
        article,
        title=normalized_title,
        raw_text=normalized_text,
        published_date=iso_date,
    )


def batch_normalize(articles: Iterable["Article"]) -> List["Article"]:
    """Normalize a list of articles defensively.

    Any article that fails normalization is skipped with a warning.
    """
    normalized: List["Article"] = []
    for a in articles:
        try:
            normalized.append(normalize_article(a))
        except Exception as exc:  # noqa: BLE001 - defensive
            _logger.warning("Failed to normalize article '%s': %s", getattr(a, "title", "?"), exc)
    return normalized


def parse_date_to_iso(value: str | datetime | None) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    # naive fallback for simple formats; robust parsing can be added later
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).isoformat()
        except Exception:
            continue
    return None
