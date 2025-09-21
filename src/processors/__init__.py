"""Processing pipeline: normalization, deduplication, classification, summarization."""

from .normalize import clean_html_to_text, parse_date_to_iso
from .dedup import Deduplicator
from .classify import classify_text
from .summarize import summarize_text

__all__ = [
    "clean_html_to_text",
    "parse_date_to_iso",
    "Deduplicator",
    "classify_text",
    "summarize_text",
]
