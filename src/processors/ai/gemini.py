from __future__ import annotations

import os
from typing import Tuple

import requests

from .base import AIClient


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
            "Classify the following text into exactly one of: Agile, DevOps, "
            "Architecture/Infra, Leadership. Respond ONLY as JSON object with keys "
            "category and confidence (0-1).\n\nTEXT:\n" + text
        )
        raw = self._generate(prompt)
        import json, re

        json_str = raw
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            json_str = match.group(0)
        obj = json.loads(json_str)
        category = str(obj.get("category", "Architecture/Infra"))
        confidence = float(obj.get("confidence", 0.0))
        return category, confidence

    def summarize(self, text: str, *, max_words: int = 150) -> str:
        prompt = (
            f"Summarize the following text in at most {max_words} words. "
            "Preserve the original language. Provide 2-3 concise sentences.\n\nTEXT:\n" + text
        )
        return self._generate(prompt)
