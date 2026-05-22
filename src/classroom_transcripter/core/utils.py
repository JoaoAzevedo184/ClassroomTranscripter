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


# Caracteres proibidos em nomes de arquivo/pasta.
#
# Grupo 1 (filesystem): < > : " / \ | ? *
#   Windows reserva esse conjunto; macOS/Linux aceitam alguns deles, mas
#   removemos pra garantir portabilidade dos vaults entre sistemas.
#
# Grupo 2 (Obsidian wikilinks): # ^ [ ]
#   Sintaticamente válidos no filesystem, mas o Obsidian usa esses chars como
#   delimitadores em [[wikilinks#heading^block|alias]]. Se um nome de arquivo
#   tiver "#", o wikilink [[001 - Aula #5]] quebra (vira link pra "001 - Aula"
#   com heading anchor "5"). Mesmo problema com ^ (block ref) e [ ] (wikilink).
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*#^\[\]]')

# Nomes reservados do Windows (case-insensitive). Se um curso/aula se chamar
# exatamente "CON" ou "NUL", o Windows recusa criar o arquivo.
_RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Remove caracteres inválidos para nomes de arquivo/pasta.

    Cobre dois conjuntos:
      1. Chars reservados do filesystem (Windows): < > : " / \\ | ? *
      2. Chars que quebram wikilinks do Obsidian: # ^ [ ]

    Também:
      - Colapsa whitespace em espaço único
      - Remove pontos/espaços do final (Windows não aceita)
      - Trata nomes reservados do Windows (CON, NUL, COM1, etc) prefixando com "_"
      - Trunca em max_length

    >>> sanitize_filename('Aula 1: Introdução ao "Docker"')
    'Aula 1 Introdução ao Docker'
    >>> sanitize_filename('Aula #5 - C++ [vector]')
    'Aula 5 - C++ vector'
    >>> sanitize_filename('Bloco ^abc')
    'Bloco abc'
    >>> sanitize_filename('CON')
    '_CON'
    >>> sanitize_filename('Aula 1.')
    'Aula 1'
    """
    if not name:
        return "_"

    # 1. Remove chars inválidos (filesystem + Obsidian)
    name = _INVALID_FILENAME_CHARS.sub("", name)

    # 2. Colapsa whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # 3. Remove pontos/espaços finais (Windows trim automático que causa bugs)
    name = name.rstrip(". ")

    # 4. Trata nomes reservados do Windows
    if name.upper() in _RESERVED_WINDOWS_NAMES:
        name = f"_{name}"

    # 5. Fallback se sobrou string vazia
    if not name:
        return "_"

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