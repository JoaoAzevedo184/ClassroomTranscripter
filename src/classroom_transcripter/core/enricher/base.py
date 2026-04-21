"""Interface base para provedores de LLM.

Contém também o helper compartilhado `_post_with_retry` que trata 429
automaticamente (extraído dos providers Groq/Gemini do v0.1).
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface para provedores de LLM."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Envia prompt e retorna resposta da LLM."""

    @abstractmethod
    def name(self) -> str:
        """Nome do provider pra logs."""

    # ─── Helper compartilhado (extraído no v0.1, mantido no v0.2) ──────

    def _post_with_retry(
        self,
        url: str,
        headers: dict,
        payload: dict,
        timeout: int = 300,
        max_retries: int = 3,
        provider_label: str = "",
    ) -> dict:
        """POST com retry automático em caso de rate limit (429).

        Usado por providers que falam HTTP JSON direto (Groq, Gemini, Claude).
        Ollama tem lógica própria pois é stream-friendly e local.
        """
        import requests

        label = provider_label or self.name()

        for attempt in range(max_retries + 1):
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

            if resp.status_code == 429 and attempt < max_retries:
                retry_after = resp.headers.get("retry-after", "60")
                wait = min(int(float(retry_after)), 120)
                print(
                    f"\n   ⏳ Rate limit atingido. Aguardando {wait}s... ",
                    end="",
                    flush=True,
                )
                time.sleep(wait)
                print("retomando")
                continue

            if not resp.ok:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get("error", {}).get("message", resp.text[:500])
                except Exception:
                    error_msg = resp.text[:500]

                if resp.status_code == 429:
                    raise RuntimeError(
                        f"{label} rate limit excedido após {max_retries} tentativas. "
                        "Aumente --delay ou tente novamente amanhã."
                    )
                raise RuntimeError(f"{label} API {resp.status_code}: {error_msg}")

            return resp.json()

        raise RuntimeError(f"{label}: número máximo de tentativas excedido.")


# Alias descritivo — usado nos docstrings da Fase 1. Ambos os nomes funcionam.
AIProvider = LLMProvider
