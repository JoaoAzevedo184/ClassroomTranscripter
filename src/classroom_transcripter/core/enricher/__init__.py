"""Enriquecimento de transcrições com IA.

Agnóstico de plataforma: enriquece qualquer `.md` gerado por qualquer source.
Providers suportados: Groq, Gemini, Ollama, Claude.
"""
from classroom_transcripter.core.enricher.base import AIProvider
from classroom_transcripter.core.enricher.pipeline import enrich_directory, enrich_file

__all__ = ["AIProvider", "create_provider", "enrich_directory", "enrich_file"]


def create_provider(name: str, **kwargs) -> AIProvider:
    """Factory: 'groq' | 'gemini' | 'ollama' | 'claude'.

    Imports são lazy: só importa a lib do provider escolhido.
    """
    name = name.lower()
    if name == "groq":
        from classroom_transcripter.core.enricher.providers.groq import GroqProvider
        return GroqProvider(**kwargs)
    if name == "gemini":
        from classroom_transcripter.core.enricher.providers.gemini import GeminiProvider
        return GeminiProvider(**kwargs)
    if name == "ollama":
        from classroom_transcripter.core.enricher.providers.ollama import OllamaProvider
        return OllamaProvider(**kwargs)
    if name == "claude":
        from classroom_transcripter.core.enricher.providers.claude import ClaudeProvider
        return ClaudeProvider(**kwargs)
    raise ValueError(
        f"Provider desconhecido: {name!r}. Opções: groq, gemini, ollama, claude"
    )
