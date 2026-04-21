"""Provider via Google Gemini API (OpenAI-compatible, tier free sem cartão)."""
from __future__ import annotations

import os

from classroom_transcripter.core.enricher.base import LLMProvider
from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError


class GeminiProvider(LLMProvider):
    """Google Gemini API (tier gratuito sem cartão de crédito).

    Modelos recomendados:
    - gemini-2.5-flash (padrão, melhor custo-benefício no free tier)
    - gemini-2.5-pro (mais capaz, limite menor: 5 RPM / 100 RPD)
    - gemini-2.5-flash-lite (mais leve, limites mais altos)
    """

    GEMINI_API_URL = (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        raw_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ProviderAPIKeyMissingError(
                "GEMINI_API_KEY não encontrada. "
                "Obtenha em aistudio.google.com e defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"gemini/{self.model}"

    def complete(self, system: str, user: str) -> str:
        data = self._post_with_retry(
            url=self.GEMINI_API_URL,
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
            provider_label="Gemini",
        )
        return data["choices"][0]["message"]["content"]
