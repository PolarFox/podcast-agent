from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Tuple

from ..models import Article


@dataclass(slots=True)
class PrioritizedItem:
    article: Article
    score: float
    rationale: str


def _source_authority(source_name: str) -> float:
    # Basic heuristic; could be extended/configured
    ranked = {
        "ThoughtWorks Technology Radar": 1.0,
        "Martin Fowler Blog": 0.9,
        "DORA DevOps Blog": 0.85,
    }
    return ranked.get(source_name, 0.6)


def _recency_boost(published_iso: str | None, *, horizon_days: int) -> float:
    if not published_iso:
        return 0.5
    try:
        dt = datetime.fromisoformat(published_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        return 0.5
    age_days = max(0, (datetime.now(timezone.utc) - dt).days)
    if age_days >= horizon_days:
        return 0.2
    # Linear decay within horizon
    return 1.0 - (age_days / horizon_days) * 0.8  # min 0.2 within horizon


def _novelty_boost(title: str) -> float:
    # Placeholder: favor longer, specific titles slightly
    length = len((title or "").split())
    return min(1.0, 0.5 + length / 20.0)


def _category_balance_weight(category: str | None) -> float:
    if not category:
        return 0.6
    # Light preference to diversify
    base = {
        "Agile": 0.9,
        "DevOps": 0.95,
        "Architecture/Infra": 1.0,
        "Leadership": 0.9,
    }.get(category, 0.8)
    return base


def prioritize_articles(
    articles: Iterable[Article], *, horizon_weeks: int = 4, top_n: int = 10
) -> List[PrioritizedItem]:
    horizon_days = max(7, horizon_weeks * 7)
    items: List[PrioritizedItem] = []
    for art in articles:
        recency = _recency_boost(art.published_date, horizon_days=horizon_days)
        authority = _source_authority(art.source)
        novelty = _novelty_boost(art.title)
        balance = _category_balance_weight(art.category)
        score = 0.4 * recency + 0.3 * authority + 0.2 * novelty + 0.1 * balance
        rationale = (
            f"recency={recency:.2f}, authority={authority:.2f}, novelty={novelty:.2f}, balance={balance:.2f}"
        )
        items.append(PrioritizedItem(article=art, score=score, rationale=rationale))
    items.sort(key=lambda x: (x.score, x.article.title.lower()), reverse=True)
    return items[:top_n]


def _month_slug(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def generate_monthly_analysis_markdown(items: List[PrioritizedItem], *, horizon_weeks: int) -> str:
    now = datetime.now(timezone.utc)
    month_name = calendar.month_name[now.month]
    lines: List[str] = []
    lines.append(f"# Situational Analysis – {month_name} {now.year}")
    lines.append("")
    lines.append(f"Planning horizon: {horizon_weeks} weeks")
    lines.append("")
    lines.append("| Rank | Score | Category | Title | Source |")
    lines.append("| ---- | -----:| -------- | ----- | ------ |")
    for idx, it in enumerate(items, start=1):
        a = it.article
        title_md = f"[{a.title}]({a.url})"
        lines.append(
            f"| {idx} | {it.score:.2f} | {a.category or '-'} | {title_md} | {a.source} |"
        )
    lines.append("")
    lines.append("## Rationale")
    for idx, it in enumerate(items, start=1):
        lines.append(f"- {idx}. {it.article.title}: {it.rationale}")
    lines.append("")
    lines.append("## Recommendations")
    lines.append(
        "Aim for balanced coverage across Architecture/Infra, DevOps, Agile, and Leadership over the next month."
    )
    return "\n".join(lines) + "\n"


def write_monthly_analysis_file(
    items: List[PrioritizedItem], *, out_dir: Path | str = "docs/analysis", horizon_weeks: int = 4
) -> Path:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = _month_slug(now)
    file_path = out_path / f"situational-{slug}.md"
    content = generate_monthly_analysis_markdown(items, horizon_weeks=horizon_weeks)
    file_path.write_text(content, encoding="utf-8")
    return file_path
