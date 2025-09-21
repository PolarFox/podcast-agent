"""Content fetching layer for RSS and HTTP sources."""

from .rss import fetch_rss_entries
from .http import fetch_http_entries

__all__ = ["fetch_rss_entries", "fetch_http_entries"]
