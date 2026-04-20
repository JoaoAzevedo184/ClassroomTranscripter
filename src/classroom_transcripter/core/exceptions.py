"""Hierarquia de exceções do Classroom Transcripter.

Toda exceção customizada herda de `TranscripterError` pra facilitar catch genérico.
Cada source pode criar subclasses específicas dela.
"""
from __future__ import annotations


class TranscripterError(Exception):
    """Base de todas as exceções do projeto."""


# --- Autenticação / acesso ---

class AuthenticationError(TranscripterError):
    """Cookie/token inválido, expirado ou ausente."""


class AccessDeniedError(TranscripterError):
    """Usuário autenticado mas sem acesso ao curso (não matriculado)."""


# --- Rede / API ---

class NetworkError(TranscripterError):
    """Falha de rede, timeout, proxy, Cloudflare challenge, etc."""


class RateLimitError(NetworkError):
    """HTTP 429 ou equivalente."""


# --- Dados / parsing ---

class CourseNotFoundError(TranscripterError):
    """Slug/URL não resolveu pra um curso válido."""


class TranscriptNotAvailableError(TranscripterError):
    """Aula existe mas não tem transcript disponível (ex: sem legendas)."""


class ParseError(TranscripterError):
    """Falha ao parsear VTT, HTML, JSON de resposta da API, etc."""


# --- Configuração ---

class ConfigurationError(TranscripterError):
    """`.env` malformado, variável obrigatória ausente, path inválido."""


# --- IA / enricher ---

class ProviderError(TranscripterError):
    """Falha no provider de IA (Groq/Gemini/Ollama/Claude)."""


class ProviderAPIKeyMissingError(ProviderError, ConfigurationError):
    """API key do provider ausente quando necessária."""
