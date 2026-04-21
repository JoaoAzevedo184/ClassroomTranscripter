"""Hierarquia de exceções do Classroom Transcripter.

Raiz: `TranscripterError`.
Todas as subclasses preservam as mensagens default do v0.1 quando aplicável.

Mapeamento v0.1 → v0.2:
    UdemyTranscripterError → TranscripterError
    AuthenticationError    → AuthenticationError  (mantém nome e mensagem)
    CloudflareBlockError   → CloudflareBlockError (mantém — é Udemy-específico)
    NoCaptionsError        → TranscriptNotAvailableError (renomeado, mais genérico)
"""
from __future__ import annotations


class TranscripterError(Exception):
    """Base de todas as exceções do projeto."""


# ─── Autenticação / acesso ──────────────────────────────────────────────────


class AuthenticationError(TranscripterError):
    """Token/cookie inválido ou expirado."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or "Token inválido ou expirado. Gere novos cookies no navegador."
        )


class CloudflareBlockError(TranscripterError):
    """Bloqueio do Cloudflare (403 com challenge page) — específico da Udemy."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message
            or (
                "Acesso negado (Cloudflare). Possíveis causas:\n"
                "  1. Cookies expirados — copie novos do navegador\n"
                "  2. Curso não comprado — verifique se você tem acesso\n"
                "  3. cf_clearance ausente — copie TODOS os cookies do header Cookie"
            )
        )


class AccessDeniedError(TranscripterError):
    """Usuário autenticado mas sem acesso ao curso (não matriculado)."""


# ─── Rede / API ─────────────────────────────────────────────────────────────


class NetworkError(TranscripterError):
    """Falha de rede, timeout, proxy, etc."""


class RateLimitError(NetworkError):
    """HTTP 429 ou equivalente."""


# ─── Dados / parsing ────────────────────────────────────────────────────────


class CourseNotFoundError(TranscripterError):
    """Slug/URL não resolveu pra um curso válido."""


class TranscriptNotAvailableError(TranscripterError):
    """Aula/curso sem transcrição disponível (substitui NoCaptionsError)."""

    def __init__(self, message: str | None = None):
        super().__init__(message or "Nenhuma transcrição encontrada.")


# Alias retrocompatível para scripts antigos que capturam NoCaptionsError.
# Será removido em v0.3. Novo código deve usar TranscriptNotAvailableError.
NoCaptionsError = TranscriptNotAvailableError


class ParseError(TranscripterError):
    """Falha ao parsear VTT, HTML, JSON de resposta, etc."""


# ─── Configuração ───────────────────────────────────────────────────────────


class ConfigurationError(TranscripterError):
    """`.env` malformado ou variável obrigatória ausente."""


# ─── IA / enricher ──────────────────────────────────────────────────────────


class ProviderError(TranscripterError):
    """Falha no provider de IA (Groq/Gemini/Ollama/Claude)."""


class ProviderAPIKeyMissingError(ProviderError, ConfigurationError):
    """API key do provider ausente."""
