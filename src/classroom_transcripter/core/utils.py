"""Funções utilitárias compartilhadas (agnósticas de plataforma)."""
from __future__ import annotations

import re

from classroom_transcripter.core.config import LANG_PRIORITY
from classroom_transcripter.core.models import Caption


def extract_slug(url_or_slug: str) -> str:
    """Extrai o slug de um curso a partir de URL ou slug direto.

    Auto-detecta a plataforma pela URL. Se não reconhecer, faz fallback
    para Udemy (comportamento v0.1).

    >>> extract_slug("https://www.udemy.com/course/docker-basico/")
    'docker-basico'
    >>> extract_slug("docker-basico")
    'docker-basico'
    >>> extract_slug("https://cursos.alura.com.br/course/docker-fundamentos")
    'docker-fundamentos'
    """
    # Import local pra evitar ciclo (platforms → utils → platforms).
    from classroom_transcripter.core.platforms import detect_platform
    return detect_platform(url_or_slug).extract_slug(url_or_slug)


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Remove caracteres inválidos para nomes de arquivo.

    >>> sanitize_filename('Aula 1: Introdução ao "Docker"')
    'Aula 1 Introdução ao Docker'
    """
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_length]


def pick_caption(
    captions: list[Caption],
    preferred_lang: str | None = None,
) -> Caption | None:
    """Escolhe a melhor legenda disponível baseado na preferência de idioma.

    Prioridade: idioma explícito > LANG_PRIORITY > primeira disponível.
    """
    if not captions:
        return None

    if preferred_lang:
        for cap in captions:
            if cap.locale.lower().startswith(preferred_lang.lower()):
                return cap

    for lang in LANG_PRIORITY:
        for cap in captions:
            if cap.locale.lower().startswith(lang.lower()):
                return cap

    return captions[0]
