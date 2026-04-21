"""Enriquecimento de transcrições com IA (agnóstico de plataforma).

Providers: Ollama (local), Groq (free/nuvem), Gemini (free/nuvem), Claude (pago).
"""
from __future__ import annotations

from classroom_transcripter.core.enricher.base import AIProvider, LLMProvider
from classroom_transcripter.core.enricher.pipeline import (
    ENRICH_USER_TEMPLATE,
    SYSTEM_PROMPT,
    EnrichResult,
    enrich_directory,
    enrich_file,
    is_enriched,
)

__all__ = [
    "AIProvider",
    "LLMProvider",
    "EnrichResult",
    "SYSTEM_PROMPT",
    "ENRICH_USER_TEMPLATE",
    "create_provider",
    "enrich_directory",
    "enrich_file",
    "is_enriched",
]


def create_provider(
    provider_name: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: int = 900,
) -> LLMProvider:
    """Factory de LLMProvider pelo nome.

    Args:
        provider_name: "ollama" | "claude" | "groq" | "gemini".
        model: nome do modelo (padrão depende do provider).
        api_key: API key (necessária para claude/groq/gemini).
        base_url: URL base (customização do Ollama).
        timeout: timeout por requisição em segundos (relevante pro Ollama).

    Imports são lazy: só importa a lib/módulo do provider escolhido.
    """
    name = provider_name.lower()

    if name == "ollama":
        from classroom_transcripter.core.enricher.providers.ollama import OllamaProvider
        kwargs: dict = {"timeout": timeout}
        if model:
            kwargs["model"] = model
        if base_url:
            kwargs["base_url"] = base_url
        return OllamaProvider(**kwargs)

    if name == "claude":
        from classroom_transcripter.core.enricher.providers.claude import ClaudeProvider
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return ClaudeProvider(**kwargs)

    if name == "groq":
        from classroom_transcripter.core.enricher.providers.groq import GroqProvider
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return GroqProvider(**kwargs)

    if name == "gemini":
        from classroom_transcripter.core.enricher.providers.gemini import GeminiProvider
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return GeminiProvider(**kwargs)

    raise ValueError(
        f"Provider '{provider_name}' não suportado. "
        "Use 'ollama', 'claude', 'groq' ou 'gemini'."
    )
