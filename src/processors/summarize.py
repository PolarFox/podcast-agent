from __future__ import annotations

from .ai import AIClient, create_ai_client
from .ai.retry import summarize_with_retry
from ..utils.logging import get_logger

logger = get_logger("ja.processors.summarize")


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]) if len(words) > max_words else text


def _build_summary_prompt(_: str, *, max_words: int) -> str:  # deprecated; clients build their own prompts
    return ""  # kept for backward compatibility


def _split_into_word_chunks(text: str, *, max_words_per_chunk: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words_per_chunk:
        return [text]
    chunks: list[str] = []
    for i in range(0, len(words), max_words_per_chunk):
        chunk_words = words[i : i + max_words_per_chunk]
        chunks.append(" ".join(chunk_words))
    return chunks


def summarize_text(text: str, *, ai: AIClient | None = None, max_words: int = 150) -> str:
    if ai is None:
        ai = create_ai_client()

    # Chunk long content to improve summary quality and avoid context overflow
    MAX_WORDS_PER_CHUNK = int(os.getenv("AI_SUMMARY_CHUNK_WORDS", "300"))
    words = text.split()
    if len(words) > MAX_WORDS_PER_CHUNK * 2:
        chunk_texts = _split_into_word_chunks(text, max_words_per_chunk=MAX_WORDS_PER_CHUNK)
        intermediate_summaries: list[str] = []
        for chunk in chunk_texts:
            # 2-3 sentences per chunk; keep short
            intermediate = summarize_with_retry(ai, chunk, max_words=min(100, max_words))
            intermediate_summaries.append(intermediate.strip())
        combined = "\n".join(intermediate_summaries)
        summary = summarize_with_retry(ai, combined, max_words=max_words).strip()
    else:
        summary = summarize_with_retry(ai, text, max_words=max_words).strip()

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
