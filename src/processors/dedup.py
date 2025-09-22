from __future__ import annotations

import difflib
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from ..models import Article
from .normalize import normalize_plain_text
from dataclasses import dataclass
from collections import defaultdict

# Optional heavy deps are imported lazily
try:  # pragma: no cover - optional dependency
    import numpy as _np  # type: ignore
except Exception:  # pragma: no cover - env without numpy
    _np = None  # type: ignore


class Deduplicator:
    """Detect duplicate or near-duplicate articles.

    Strategies:
    - Persistent SHA-256 hash of normalized title+content
    - Fuzzy title matching via difflib with configurable threshold
    - Optional semantic similarity via sentence-transformers (in-memory during run)
    """

    def __init__(
        self,
        store_path: Path | str = "./.cache/seen.json",
        *,
        title_threshold: float = 0.85,
        enable_semantic: bool = True,
        semantic_threshold: float = 0.85,
        max_embeddings: int = 1000,
    ) -> None:
        # Allow environment overrides for operational tuning without code changes
        env_store = os.getenv("DEDUP_STORE_PATH")
        env_title_thr = os.getenv("DEDUP_TITLE_THRESHOLD")
        env_enable_sem = os.getenv("DEDUP_ENABLE_SEMANTIC")
        env_sem_thr = os.getenv("DEDUP_SEMANTIC_THRESHOLD")
        env_max_emb = os.getenv("DEDUP_MAX_EMBEDDINGS")

        self.store_path = Path(env_store or store_path)
        self.title_threshold = float(env_title_thr) if env_title_thr else title_threshold
        self.enable_semantic = (
            (env_enable_sem.lower() in {"1", "true", "yes"}) if env_enable_sem else enable_semantic
        )
        self.semantic_threshold = float(env_sem_thr) if env_sem_thr else semantic_threshold
        self.max_embeddings = int(env_max_emb) if env_max_emb else max_embeddings

        self._seen_hashes: set[str] = set()
        self._titles: List[str] = []
        self._embeddings: List["_np.ndarray"] = []  # type: ignore[name-defined]
        self._model = None
        self._load()

    # ---------------- Persistence -----------------
    def _load(self) -> None:
        if not self.store_path.exists():
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            self._seen_hashes = set(data.get("hashes", []))
            self._titles = list(data.get("titles", []))
        except Exception:
            self._seen_hashes = set()
            self._titles = []

    def _save(self) -> None:
        payload = {"hashes": sorted(self._seen_hashes), "titles": self._titles[-5000:]}
        self.store_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------------- Normalization helpers -----------------
    @staticmethod
    def content_hash(title: str, text: str) -> str:
        # Normalize via lightweight text normalizer to improve robustness
        # Keep legacy lowercasing behavior to avoid breaking existing caches
        t_norm = normalize_plain_text(title or "")
        x_norm = normalize_plain_text(text or "")
        normalized = t_norm.lower() + "\n\n" + x_norm.lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def similar_titles(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

    # ---------------- Semantic similarity -----------------
    def _ensure_model(self) -> None:
        if not (self.enable_semantic and _np is not None):
            return
        if self._model is not None:
            return
        try:  # lazy import to avoid heavy startup cost
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            # Disable semantic if model cannot be loaded
            self.enable_semantic = False
            self._model = None

    def _embed(self, text: str):
        self._ensure_model()
        if not self._model:
            return None
        vec = self._model.encode([text], normalize_embeddings=True)[0]
        if _np is None:
            return None
        return _np.asarray(vec)

    def _max_cosine(self, vec) -> float:
        if _np is None or not self._embeddings:
            return 0.0
        # Using matrix dot product for efficiency
        mat = _np.vstack(self._embeddings)
        sims = mat @ vec  # cosine sims because vectors are normalized
        return float(sims.max()) if sims.size else 0.0

    # ---------------- Public API -----------------
    def is_duplicate(
        self, article: Article, *, prior_titles: Iterable[str] = ()
    ) -> Tuple[bool, Optional[str]]:
        content_hash = self.content_hash(article.title, article.raw_text)
        if content_hash in self._seen_hashes:
            return True, "hash"

        # Fuzzy title match against provided titles and persisted titles
        for t in list(prior_titles) + self._titles:
            if self.similar_titles(article.title, t) >= self.title_threshold:
                return True, "title"

        # Semantic similarity (in-memory, only this run)
        if self.enable_semantic and _np is not None and article.raw_text:
            vec = self._embed(article.raw_text[:8000])  # limit very long texts
            if vec is not None and self._embeddings:
                max_sim = self._max_cosine(vec)
                if max_sim >= self.semantic_threshold:
                    return True, "semantic"
        return False, None

    def mark_seen(self, article: Article) -> None:
        content_hash = self.content_hash(article.title, article.raw_text)
        self._seen_hashes.add(content_hash)
        # Track titles for future fuzzy matching
        if article.title:
            self._titles.append(article.title.strip())
            # keep reasonable memory footprint
            if len(self._titles) > 10000:
                self._titles = self._titles[-10000:]
        # Track embedding in-memory only
        if self.enable_semantic and article.raw_text:
            vec = self._embed(article.raw_text[:8000])
            if vec is not None:
                self._embeddings.append(vec)
                if len(self._embeddings) > self.max_embeddings:
                    self._embeddings = self._embeddings[-self.max_embeddings :]
        self._save()


@dataclass(slots=True)
class DedupStats:
    total: int
    kept: int
    duplicates: int
    reasons: dict[str, int]


def remove_duplicates(
    articles: Iterable[Article],
    *,
    dedup: Optional[Deduplicator] = None,
    prior_titles: Iterable[str] = (),
    return_stats: bool = False,
):
    """Remove duplicates from an iterable of articles using Deduplicator.

    Returns a list of unique articles by default. If ``return_stats`` is True,
    returns a tuple of (unique_articles, DedupStats).
    """
    d = dedup or Deduplicator()
    unique: List[Article] = []
    reasons = defaultdict(int)
    prior_list = list(prior_titles)
    total = 0
    for art in articles:
        total += 1
        is_dup, reason = d.is_duplicate(art, prior_titles=prior_list)
        if is_dup:
            reasons[(reason or "unknown")] += 1
            continue
        d.mark_seen(art)
        if art.title:
            prior_list.append(art.title)
        unique.append(art)
    stats = DedupStats(total=total, kept=len(unique), duplicates=total - len(unique), reasons=dict(reasons))
    return (unique, stats) if return_stats else unique
