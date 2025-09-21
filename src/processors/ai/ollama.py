from __future__ import annotations

import os
from typing import Tuple

import requests

from .base import AIClient


class OllamaClient(AIClient):
    """HTTP client for Ollama's chat/completions API.

    Environment:
      - OLLAMA_HOST (default: http://localhost:11434)
      - OLLAMA_MODEL (default: llama3.1:8b-instruct)
    """

    def __init__(self) -> None:
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct")

    def _chat(self, prompt: str, *, temperature: float = 0.2, timeout: int = 60) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {'response': '...'}
        return data.get("response", "").strip()

    def classify(self, text: str) -> Tuple[str, float]:
        prompt = (
            "Classify the following text into exactly one of: Agile, DevOps, "
            "Architecture/Infra, Leadership. Respond ONLY as JSON object with keys "
            "category and confidence (0-1).\n\nTEXT:\n" + text
        )
        raw = self._chat(prompt)
        # Simple JSON extraction without extra deps
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
        return self._chat(prompt)
