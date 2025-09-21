from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

_whitespace_re = re.compile(r"\s+")


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
