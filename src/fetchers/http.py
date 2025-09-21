from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..models import Source

logger = logging.getLogger("ja.fetchers.http")


@dataclass(slots=True)
class HTTPItem:
    title: Optional[str]
    url: str
    description: Optional[str]
    content: Optional[str]


_DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    )
}


def fetch_http_entries(source: Source, *, timeout: int = 30) -> List[HTTPItem]:
    if source.type != "http":
        raise ValueError("fetch_http_entries requires a source of type 'http'")

    headers = {**_DEFAULT_HEADERS, **(source.headers or {})}
    logger.debug("Fetching HTTP content from %s", source.url)
    resp = requests.get(source.url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Very simple heuristic extraction. Real implementation will be more robust.
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None

    main = soup.find("main") or soup.body
    content = main.get_text("\n", strip=True) if main else None

    logger.info("Fetched HTTP page: %s", source.name)
    return [HTTPItem(title=title, url=source.url, description=description, content=content)]
