from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import yaml

from ..models import Source


class ConfigError(Exception):
    """Raised when the configuration file is invalid or missing required fields."""


REQUIRED_FIELDS = {"name", "url", "type"}


def _validate_source_dict(entry: dict) -> None:
    missing = REQUIRED_FIELDS - set(entry)
    if missing:
        raise ConfigError(f"Missing required fields: {sorted(missing)} in {entry}")
    if entry["type"] not in {"rss", "http"}:
        raise ConfigError(f"Invalid type '{entry['type']}'. Must be 'rss' or 'http'.")


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
    """Load sources.yaml configuration into typed Source instances.

    The YAML format is expected to be a mapping with a top-level key
    "sources" that contains a list of source objects.
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
