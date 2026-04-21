"""Provider local via Ollama API."""
from __future__ import annotations

from classroom_transcripter.core.enricher.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Provider local via Ollama API (não usa _post_with_retry — Ollama não faz 429)."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        timeout: int = 900,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def name(self) -> str:
        return f"ollama/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 16384,
                },
            },
            timeout=self.timeout,
        )

        if not resp.ok:
            try:
                error_msg = resp.json().get("error", resp.text[:500])
            except Exception:
                error_msg = resp.text[:500]
            raise RuntimeError(f"Ollama {resp.status_code}: {error_msg}")

        return resp.json()["message"]["content"]
