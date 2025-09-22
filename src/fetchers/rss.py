from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import feedparser
import requests

from ..models import Source
from ..utils.logging import get_logger

logger = get_logger("ja.fetchers.rss")


@dataclass(slots=True)
class RSSItem:
    title: str
    link: str
    description: Optional[str]
    published: Optional[datetime]
    content: Optional[str]


_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    )
}


def _parse_datetime(entry: dict) -> Optional[datetime]:
    # feedparser may provide 'published_parsed' or 'updated_parsed'
    for key in ("published_parsed", "updated_parsed"):
        tm = entry.get(key)
        if tm:
            try:
                return datetime(*tm[:6])
            except Exception:  # noqa: BLE001 - defensive parsing
                return None
    return None


def fetch_rss_entries(source: Source, *, timeout: int = 30) -> List[RSSItem]:
    """Fetch and parse RSS/Atom feed entries with timeouts and basic robustness.

    The underlying network request is done with ``requests`` to ensure
    consistent timeouts and headers. The response body is then parsed by
    ``feedparser`` to handle various feed formats.
    """
    if source.type != "rss":
        raise ValueError("fetch_rss_entries requires a source of type 'rss'")

    logger.debug("Fetching RSS from %s", source.url)
    try:
        resp = requests.get(source.url, headers=_DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code >= 400:
            logger.warning("RSS fetch failed (%s): %s", resp.status_code, source.url)
            resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except requests.RequestException as exc:
        logger.warning("RSS request error for %s: %s", source.url, exc)
        raise

    items: List[RSSItem] = []
    if getattr(parsed, "bozo", False):
        # feedparser sets bozo when it encounters a feed error but may still parse entries
        logger.debug("Feed 'bozo' flagged for %s: %s", source.url, getattr(parsed, "bozo_exception", None))

    for entry in getattr(parsed, "entries", []) or []:
        title = getattr(entry, "title", None) or ""
        link = getattr(entry, "link", None) or ""
        description = getattr(entry, "summary", None)
        published = _parse_datetime(entry)

        content_val = None
        contents = getattr(entry, "content", None)
        if contents and isinstance(contents, list) and contents:
            content_val = contents[0].get("value")

        items.append(
            RSSItem(
                title=title,
                link=link,
                description=description,
                published=published,
                content=content_val,
            )
        )

    logger.info("Fetched %d RSS entries from %s", len(items), source.name)
    return items
