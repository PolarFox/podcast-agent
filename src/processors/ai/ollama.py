from __future__ import annotations

import os
from typing import Tuple

import requests

from .base import AIClient
from .parsing import parse_classification_response


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
        # More explicit, structured instructions with clear category definitions
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
        raw = self._chat(prompt)
        return parse_classification_response(raw)

    def summarize(self, text: str, *, max_words: int = 150) -> str:
        prompt = (
            f"Summarize the following text in at most {max_words} words. "
            "Preserve the original language. Provide 2-3 concise sentences.\n\nTEXT:\n" + text
        )
        return self._chat(prompt)
