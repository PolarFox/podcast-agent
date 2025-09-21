from __future__ import annotations

import re
from typing import List

from .ai import AIClient, create_ai_client


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]) if len(words) > max_words else text


def _build_bullets_prompt(content: str, *, max_points: int, max_words_per_bullet: int) -> str:
    return (
        "You are an assistant that writes actionable team impact bullet points.\n"
        f"Task: Produce {max_points} bullet points titled 'Impact to teams' based on the article below.\n"
        f"Each bullet must be <= {max_words_per_bullet} words, start with '- ', be concise and actionable, and preserve the original language (Finnish or English).\n"
        "Return only the bullets, each on its own line, no extra text.\n\n"
        "Article:\n" + content
    )


def generate_impact_points(
    text: str,
    *,
    ai: AIClient | None = None,
    max_points: int = 3,
    max_words_per_bullet: int = 50,
) -> List[str]:
    if ai is None:
        ai = create_ai_client()

    prompt = _build_bullets_prompt(text, max_points=max_points, max_words_per_bullet=max_words_per_bullet)
    try:
        raw = ai.summarize(prompt, max_words=max_points * max_words_per_bullet)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        bullets: List[str] = []
        for ln in lines:
            ln = re.sub(r"^[-•]\s*", "", ln)  # strip leading markers
            bullets.append(_truncate_words(ln, max_words_per_bullet))
            if len(bullets) >= max_points:
                break
        if bullets:
            return bullets
    except Exception:
        pass

    # Fallback heuristic if AI fails
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    points: List[str] = []
    for s in sentences:
        if len(points) >= max_points:
            break
        if len(s.split()) >= 6:
            points.append(_truncate_words(s, max_words_per_bullet))
    if not points:
        points = ["Discuss how this affects current initiatives."]
    return points
