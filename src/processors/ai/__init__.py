"""AI backend selection and clients (Ollama, Gemini)."""

from .base import AIClient
from .factory import create_ai_client

__all__ = ["AIClient", "create_ai_client"]
