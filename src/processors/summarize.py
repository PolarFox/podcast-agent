from __future__ import annotations

import logging

from .ai import AIClient, create_ai_client

logger = logging.getLogger("ja.processors.summarize")


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]) if len(words) > max_words else text


def _build_summary_prompt(content: str, *, max_words: int) -> str:
    return (
        "You are an assistant that writes concise TL;DR summaries.\n"
        "Task: Write a TL;DR of the following article in 2-3 sentences, "
        f"no more than {max_words} words total. Preserve the original language (Finnish or English).\n\n"
        "Article:\n" + content
    )


def summarize_text(text: str, *, ai: AIClient | None = None, max_words: int = 150) -> str:
    if ai is None:
        ai = create_ai_client()

    prompt = _build_summary_prompt(text, max_words=max_words)

    summary = ai.summarize(prompt, max_words=max_words).strip()

    # Normalize to 2-3 sentences and enforce word limit
    import re

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary) if s.strip()]
    if len(sentences) == 1:
        # best-effort split on semicolons/commas if single long sentence
        parts = re.split(r"[;:,]\s+", sentences[0])
        sentences = [p.strip() for p in parts if p.strip()][:3]
    sentences = sentences[:3]
    if len(sentences) < 2 and len(text.split()) > 40:
        # ensure at least two sentences when source is non-trivial
        sentences = sentences + [""]
    out = " ".join(sentences).strip()
    return _truncate_words(out, max_words)
