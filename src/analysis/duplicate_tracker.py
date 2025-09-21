from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from ..models import Article


@dataclass(slots=True)
class IssueRecord:
    title_hash: str
    url_hashes: Tuple[str, ...]
    issue_number: Optional[int]


class DuplicateTracker:
    """File-backed tracker to prevent duplicate issue creation.

    Stores minimal identifiers: title hash and URL hashes for articles included
    in an issue.
    """

    def __init__(self, *, store_path: Path | str = ".cache/issue-history.json") -> None:
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: List[IssueRecord] = []
        self._title_index: Set[str] = set()
        self._url_index: Set[str] = set()
        self._load()

    @staticmethod
    def _hash_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            for row in data:
                rec = IssueRecord(
                    title_hash=row["title_hash"],
                    url_hashes=tuple(row.get("url_hashes") or ()),
                    issue_number=row.get("issue_number"),
                )
                self._records.append(rec)
                self._title_index.add(rec.title_hash)
                self._url_index.update(rec.url_hashes)
        except Exception:
            # Corrupt or unexpected format; start fresh
            self._records = []
            self._title_index = set()
            self._url_index = set()

    def _persist(self) -> None:
        rows = [asdict(r) for r in self._records]
        self.store_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def has_seen_articles(self, articles: Iterable[Article]) -> bool:
        title_hashes = [self._hash_text(a.title) for a in articles]
        url_hashes = [self._hash_text(a.url) for a in articles]
        return any(h in self._title_index for h in title_hashes) or any(
            h in self._url_index for h in url_hashes
        )

    def record_issue(self, *, title: str, articles: Iterable[Article], issue_number: Optional[int]) -> None:
        rec = IssueRecord(
            title_hash=self._hash_text(title),
            url_hashes=tuple(self._hash_text(a.url) for a in articles),
            issue_number=issue_number,
        )
        self._records.append(rec)
        self._title_index.add(rec.title_hash)
        self._url_index.update(rec.url_hashes)
        self._persist()
