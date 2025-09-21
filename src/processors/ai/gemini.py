from __future__ import annotations

import os
from typing import Tuple

import requests

from .base import AIClient
from .parsing import parse_classification_response


class GeminiClient(AIClient):
    """HTTP client for Gemini via Google AI Studio API.

    Environment:
      - GOOGLE_API_KEY (required)
      - GEMINI_MODEL (default: gemini-1.5-flash)
    """

    def __init__(self) -> None:
        self.api_key = os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is required for Gemini backend")
        self.model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    def _generate(self, prompt: str, *, temperature: float = 0.2, timeout: int = 60) -> str:
        # Google AI Studio text generation endpoint
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {"temperature": temperature},
        }
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # Extract text from the first candidate
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        return text.strip()

    def classify(self, text: str) -> Tuple[str, float]:
        prompt = (
            "You are a strict JSON-only classifier. "
            "Classify the ARTICLE into exactly one primary category: Agile, DevOps, Architecture/Infra, Leadership.\n\n"
            "Category guidelines:\n"
            "- Agile: Scrum, Kanban, product discovery, story points, retrospectives, team rituals, agile metrics.\n"
            "- DevOps: CI/CD, pipelines, reliability/SRE, observability, incident response, infrastructure-as-code in service of delivery.\n"
            "- Architecture/Infra: system design, distributed systems, cloud services, networking, databases, infrastructure primitives.\n"
            "- Leadership: org design, management, hiring, culture, budgets, strategy, stakeholder communication.\n\n"
            "Rules: Choose one best fit. If multiple apply, pick the primary editorial lens.\n"
            "Output MUST be a single JSON object with keys: category (string), confidence (number 0-1), reasoning (string, short).\n"
            "Do not include markdown, code fences, or extra text.\n\n"
            f"ARTICLE:\n{text}\n"
        )
        raw = self._generate(prompt)
        return parse_classification_response(raw)

    def summarize(self, text: str, *, max_words: int = 150) -> str:
        prompt = (
            f"Summarize the following text in at most {max_words} words. "
            "Preserve the original language. Provide 2-3 concise sentences.\n\nTEXT:\n" + text
        )
        return self._generate(prompt)
