"""Provider via Anthropic Claude API."""
from __future__ import annotations

import os

from classroom_transcripter.core.enricher.base import LLMProvider
from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API (pago, rápido, alta qualidade)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
    ):
        raw_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ProviderAPIKeyMissingError(
                "ANTHROPIC_API_KEY não encontrada. Defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"claude/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 8192,
                "system": system,
                "messages": [
                    {"role": "user", "content": user},
                ],
            },
            timeout=300,
        )

        if not resp.ok:
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", resp.text)
                error_type = error_data.get("error", {}).get("type", "unknown")
            except Exception:
                error_msg = resp.text[:500]
                error_type = "unknown"
            raise RuntimeError(
                f"Claude API {resp.status_code} ({error_type}): {error_msg}"
            )

        data = resp.json()
        return data["content"][0]["text"]
