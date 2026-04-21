"""Identificação de plataformas por URL.

Responsabilidade: dada uma URL, descobrir qual plataforma (`Udemy`/`DIO`/`Alura`)
ela representa e extrair o slug/identificador do curso.

Esta é a camada de ROTEAMENTO — stateless, barata, sem I/O, sem credenciais.

Para a camada que REALMENTE busca dados (com auth, HTTP, Whisper, etc.),
veja `classroom_transcripter.sources.base.TranscriptSource`.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PlatformInfo:
    """Metadados de uma plataforma suportada."""

    name: str
    base_url: str
    description: str
    requires_auth: bool = True


class BasePlatform(ABC):
    """Interface base para identificação de plataformas.

    Cada plataforma sabe:
    - Extrair um slug/identificador a partir de uma URL
    - Fornecer suas informações básicas
    - Indicar se requer autenticação
    """

    @abstractmethod
    def info(self) -> PlatformInfo:
        """Metadados da plataforma."""

    @abstractmethod
    def extract_slug(self, url: str) -> str:
        """Extrai o slug do curso.

        Args:
            url: URL completa ou slug direto.

        Returns:
            Slug/identificador do curso.
        """

    @abstractmethod
    def matches_url(self, url: str) -> bool:
        """True se a URL pertence a esta plataforma."""


class UdemyPlatform(BasePlatform):
    """Udemy."""

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Udemy",
            base_url="https://www.udemy.com",
            description="Plataforma de cursos online com autenticação por cookies",
            requires_auth=True,
        )

    def extract_slug(self, url: str) -> str:
        """
        >>> UdemyPlatform().extract_slug("https://www.udemy.com/course/docker-basico/")
        'docker-basico'
        >>> UdemyPlatform().extract_slug("docker-basico")
        'docker-basico'
        """
        match = re.search(r"udemy\.com/course/([^/?#]+)", url)
        if match:
            return match.group(1)
        return url.strip("/")

    def matches_url(self, url: str) -> bool:
        return "udemy.com" in url


class DioPlatform(BasePlatform):
    """DIO (Digital Innovation One).

    Como DIO depende de Whisper local, o "identifier" NÃO é uma URL mas sim
    um path pra pasta do bootcamp baixado. Mesmo assim, mantemos URL matching
    pra mensagens de erro amigáveis ("use um path local, não URL").
    """

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="DIO",
            base_url="https://web.dio.me",
            description="Bootcamps com transcrição via Whisper local (requer .mp4 baixado)",
            requires_auth=False,  # DIO só lê arquivos locais
        )

    def extract_slug(self, url_or_path: str) -> str:
        """
        >>> DioPlatform().extract_slug("/home/user/dio_videos/jornada-node")
        'jornada-node'
        >>> DioPlatform().extract_slug("jornada-node")
        'jornada-node'
        """
        # Se for URL da DIO, extrai a última parte
        match = re.search(r"dio\.me/(?:track|course|bootcamp)/([^/?#]+)", url_or_path)
        if match:
            return match.group(1)
        # Senão, último componente do path (Path-like ou slug)
        return url_or_path.rstrip("/").split("/")[-1]

    def matches_url(self, url: str) -> bool:
        return "dio.me" in url


class AluraPlatform(BasePlatform):
    """Alura."""

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="Alura",
            base_url="https://cursos.alura.com.br",
            description="Cursos com transcrição oficial via login (email/senha)",
            requires_auth=True,
        )

    def extract_slug(self, url: str) -> str:
        """
        >>> AluraPlatform().extract_slug("https://cursos.alura.com.br/course/docker-fundamentos")
        'docker-fundamentos'
        >>> AluraPlatform().extract_slug("docker-fundamentos")
        'docker-fundamentos'
        """
        match = re.search(r"alura\.com\.br/course/([^/?#]+)", url)
        if match:
            return match.group(1)
        return url.strip("/")

    def matches_url(self, url: str) -> bool:
        return "alura.com.br" in url


# ─── Registry ───────────────────────────────────────────────────────────────

PLATFORMS: dict[str, type[BasePlatform]] = {
    "udemy": UdemyPlatform,
    "dio": DioPlatform,
    "alura": AluraPlatform,
}


def get_platform(name: str) -> BasePlatform:
    """Retorna instância pelo nome ('udemy' | 'dio' | 'alura')."""
    cls = PLATFORMS.get(name.lower())
    if cls is None:
        available = ", ".join(PLATFORMS.keys())
        raise ValueError(f"Plataforma '{name}' não suportada. Disponíveis: {available}")
    return cls()


def detect_platform(url: str) -> BasePlatform:
    """Detecta plataforma pela URL. Fallback: Udemy (comportamento v0.1)."""
    for cls in PLATFORMS.values():
        platform = cls()
        if platform.matches_url(url):
            return platform
    return UdemyPlatform()
