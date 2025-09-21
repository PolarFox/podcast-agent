from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

import feedparser

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
    if source.type != "rss":
        raise ValueError("fetch_rss_entries requires a source of type 'rss'")

    logger.debug("Fetching RSS from %s", source.url)
    parsed = feedparser.parse(source.url)

    items: List[RSSItem] = []
    for entry in parsed.entries:
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
