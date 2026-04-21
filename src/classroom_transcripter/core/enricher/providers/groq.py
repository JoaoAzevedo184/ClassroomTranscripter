"""Provider via Groq API (OpenAI-compatible, ultra-rápido, tier free)."""
from __future__ import annotations

import os

from classroom_transcripter.core.enricher.base import LLMProvider
from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError


class GroqProvider(LLMProvider):
    """Groq API via LPUs (inferência ultra-rápida, tier gratuito sem cartão).

    Modelos recomendados:
    - llama-3.3-70b-versatile (padrão, melhor qualidade)
    - llama-3.1-8b-instant (mais rápido)
    - deepseek-r1-distill-llama-70b (raciocínio/código)
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        raw_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ProviderAPIKeyMissingError(
                "GROQ_API_KEY não encontrada. "
                "Obtenha em console.groq.com e defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"groq/{self.model}"

    def complete(self, system: str, user: str) -> str:
        data = self._post_with_retry(
            url=self.GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.3,
                "max_completion_tokens": 8192,
            },
            provider_label="Groq",
        )
        return data["choices"][0]["message"]["content"]
