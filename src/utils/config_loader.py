from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
from urllib.parse import urlparse

import yaml

from ..models import Source


class ConfigError(Exception):
    """Raised when the configuration file is invalid or missing required fields."""


REQUIRED_FIELDS = {"name", "url", "type"}

# Accepted categories used across the pipeline. These map to
# analysis and classification outputs. Kept here for lightweight
# validation of configuration files to catch typos early.
ALLOWED_CATEGORIES = {"Agile", "DevOps", "Architecture/Infra", "Leadership"}


def _validate_source_dict(entry: dict) -> None:
    """Validate a single source mapping from YAML.

    Required fields: name (str), url (http/https), type ('rss' | 'http').
    Optional fields:
      - keywords: list[str]
      - category_hints: list[str] from ALLOWED_CATEGORIES
      - headers: mapping[str, str] (for HTTP sources)
    """
    missing = REQUIRED_FIELDS - set(entry)
    if missing:
        raise ConfigError(f"Missing required fields: {sorted(missing)} in {entry}")

    # type
    if entry["type"] not in {"rss", "http"}:
        raise ConfigError(f"Invalid type '{entry['type']}'. Must be 'rss' or 'http'.")

    # url
    url_str = str(entry["url"]).strip()
    parsed = urlparse(url_str)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ConfigError(f"Invalid URL '{url_str}'. Must be absolute http(s) URL.")

    # keywords
    if "keywords" in entry and entry["keywords"] is not None:
        kws = entry["keywords"]
        if not isinstance(kws, list) or not all(isinstance(k, (str, bytes)) for k in kws):
            raise ConfigError("'keywords' must be a list of strings if provided")

    # category_hints
    if "category_hints" in entry and entry["category_hints"] is not None:
        hints = entry["category_hints"]
        if not isinstance(hints, list) or not all(isinstance(c, (str, bytes)) for c in hints):
            raise ConfigError("'category_hints' must be a list of strings if provided")
        invalid = [str(c) for c in hints if str(c) not in ALLOWED_CATEGORIES]
        if invalid:
            raise ConfigError(
                "Invalid category_hints: "
                + ", ".join(sorted(set(invalid)))
                + f". Allowed: {sorted(ALLOWED_CATEGORIES)}"
            )

    # headers
    if "headers" in entry and entry["headers"] is not None:
        headers = entry["headers"]
        if not isinstance(headers, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items()):
            raise ConfigError("'headers' must be a mapping of string keys to string values if provided")


def _coerce_source(entry: dict) -> Source:
    keywords = entry.get("keywords") or []
    category_hints = entry.get("category_hints") or []
    headers = entry.get("headers") or {}
    return Source(
        name=str(entry["name"]).strip(),
        url=str(entry["url"]).strip(),
        type=str(entry["type"]).strip(),
        keywords=[str(k).strip() for k in keywords],
        category_hints=[str(c).strip() for c in category_hints],
        headers={str(k): str(v) for k, v in headers.items()},
    )


def load_sources_config(path: Path | str) -> List[Source]:
    """Load ``sources.yaml`` into typed ``Source`` instances.

    YAML structure:
      - Top-level mapping
      - Key ``sources``: list of source mappings with fields
          - name: string (required)
          - url: http/https URL (required)
          - type: 'rss' | 'http' (required)
          - keywords: list[string] (optional)
          - category_hints: list['Agile'|'DevOps'|'Architecture/Infra'|'Leadership'] (optional)
          - headers: mapping[string, string] (optional, for HTTP fetcher)

    Unknown top-level keys are ignored for forward compatibility.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    sources_raw: Iterable[dict] = (data.get("sources") or [])
    if not isinstance(sources_raw, list):
        raise ConfigError("'sources' must be a list in the YAML configuration")

    sources: List[Source] = []
    for item in sources_raw:
        if not isinstance(item, dict):
            raise ConfigError(f"Each source must be a mapping, got: {type(item)}")
        _validate_source_dict(item)
        sources.append(_coerce_source(item))
    return sources
