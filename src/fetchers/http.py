from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ..models import Source
from ..utils.logging import get_logger

logger = get_logger("ja.fetchers.http")


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

def _validated_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Invalid URL for HTTP fetch: {url}")
    return url


def fetch_http_entries(source: Source, *, timeout: int = 30) -> List[HTTPItem]:
    if source.type != "http":
        raise ValueError("fetch_http_entries requires a source of type 'http'")

    headers = {**_DEFAULT_HEADERS, **(source.headers or {})}
    url = _validated_url(source.url)
    logger.debug("Fetching HTTP content from %s", url)
    resp = requests.get(url, headers=headers, timeout=timeout)
    if resp.status_code >= 400:
        logger.warning("HTTP fetch failed (%s): %s", resp.status_code, source.url)
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
