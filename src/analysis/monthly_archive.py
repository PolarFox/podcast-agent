from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from ..models import Article
from ..utils.logging import get_logger


logger = get_logger("ja.analysis.archive")


class MonthlyArchive:
    """JSON file-backed storage for processed articles grouped by month.

    Files are stored under base_dir/YYYY-MM.json. Writes are idempotent and
    merge new articles by URL.
    """

    def __init__(self, base_dir: str | Path = "data/archive") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _month_slug(self, dt: Optional[datetime] = None) -> str:
        dt = dt or datetime.now(timezone.utc)
        return f"{dt.year:04d}-{dt.month:02d}"

    def _file_for_month(self, month_slug: str) -> Path:
        return self.base_dir / f"{month_slug}.json"

    @staticmethod
    def _article_to_dict(a: Article) -> dict:
        obj = asdict(a)
        # Keep minimal necessary fields with stable names
        return {
            "title": obj.get("title"),
            "url": obj.get("url"),
            "source": obj.get("source"),
            "raw_text": obj.get("raw_text"),
            "published_date": obj.get("published_date"),
            "category": obj.get("category"),
            "summary": obj.get("summary"),
            "confidence_score": obj.get("confidence_score"),
        }

    @staticmethod
    def _dict_to_article(d: dict) -> Article:
        return Article(
            title=d.get("title") or "",
            url=d.get("url") or "",
            source=d.get("source") or "",
            raw_text=d.get("raw_text") or "",
            published_date=d.get("published_date"),
            category=d.get("category"),
            summary=d.get("summary"),
            confidence_score=d.get("confidence_score"),
        )

    def store_articles(self, articles: Iterable[Article], *, month_slug: Optional[str] = None) -> Path:
        """Merge and store articles for the given month (defaults to current)."""
        slug = month_slug or self._month_slug()
        file_path = self._file_for_month(slug)

        existing: dict[str, dict] = {}
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                for row in data.get("articles", []):
                    if isinstance(row, dict):
                        url = row.get("url")
                        if url:
                            existing[url] = row
            except Exception:  # noqa: BLE001
                logger.warning("Archive file corrupted; recreating: %s", file_path)
                existing = {}

        for art in articles:
            d = self._article_to_dict(art)
            existing[d["url"]] = d

        payload = {
            "month": slug,
            "count": len(existing),
            "articles": list(existing.values()),
        }
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Stored %d article(s) to %s", len(existing), file_path)
        return file_path

    def load_monthly_articles(self, *, month_slug: Optional[str] = None) -> List[Article]:
        slug = month_slug or self._month_slug()
        file_path = self._file_for_month(slug)
        if not file_path.exists():
            return []
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return [self._dict_to_article(row) for row in data.get("articles", []) if isinstance(row, dict)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load archive %s: %s", file_path, exc)
            return []

    def list_archives(self) -> List[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.json"))
