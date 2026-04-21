"""Configurações, constantes e carregamento de variáveis de ambiente.

Multi-plataforma na v0.2: além das constantes da Udemy (mantidas),
adicionadas variáveis para DIO (Whisper) e Alura.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════════════════════════
# UDEMY — constantes da API interna (mantidas do v0.1)
# ═══════════════════════════════════════════════════════════════════════════

UDEMY_BASE_URL = "https://www.udemy.com"
UDEMY_API_BASE = f"{UDEMY_BASE_URL}/api-2.0"

UDEMY_HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": UDEMY_BASE_URL,
}

# Aliases v0.1 (`BASE_URL`, `API_BASE`, `HEADERS_BASE`) mantidos abaixo
# por enquanto pra facilitar migração de qualquer import que reste.
# Remover em v0.3.
BASE_URL = UDEMY_BASE_URL
API_BASE = UDEMY_API_BASE
HEADERS_BASE = UDEMY_HEADERS_BASE

# Tamanho de página do endpoint de curriculum da Udemy
CURRICULUM_PAGE_SIZE = 200


# ═══════════════════════════════════════════════════════════════════════════
# GERAL — rate limit / idiomas
# ═══════════════════════════════════════════════════════════════════════════

# Delay entre downloads de legendas (em segundos)
DOWNLOAD_DELAY = 0.3

# Prioridade padrão de idiomas para escolher caption quando --lang não é passado
_DEFAULT_LANG_PRIORITY = ["pt", "pt-BR", "en", "en_US", "en_GB", "es"]


def get_lang_priority() -> list[str]:
    """Retorna a ordem de preferência de idiomas para legendas.

    Lê de LANG_PRIORITY no .env (ex: LANG_PRIORITY=pt,en,es).
    Fallback: pt, pt-BR, en, en_US, en_GB, es.
    """
    raw = os.getenv("LANG_PRIORITY", "")
    if raw.strip():
        return [lang.strip() for lang in raw.split(",") if lang.strip()]
    return list(_DEFAULT_LANG_PRIORITY)


# Valor estático resolvido na importação. Para comportamento dinâmico
# (mudar LANG_PRIORITY em runtime), use get_lang_priority().
LANG_PRIORITY = get_lang_priority()


# ═══════════════════════════════════════════════════════════════════════════
# DIO — transcrição local com Whisper (v0.2)
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_DIO_VIDEO_DIR = Path("./dio_videos")
DEFAULT_WHISPER_MODEL = "small"  # tiny | base | small | medium | large
DEFAULT_WHISPER_LANGUAGE = "pt"


def get_dio_video_dir() -> Path:
    return Path(os.getenv("DIO_VIDEO_DIR") or DEFAULT_DIO_VIDEO_DIR)


def get_whisper_model() -> str:
    return os.getenv("WHISPER_MODEL") or DEFAULT_WHISPER_MODEL


def get_whisper_language() -> str:
    return os.getenv("WHISPER_LANGUAGE") or DEFAULT_WHISPER_LANGUAGE


# ═══════════════════════════════════════════════════════════════════════════
# ALURA — credenciais (v0.2)
# ═══════════════════════════════════════════════════════════════════════════

def get_alura_credentials() -> tuple[str, str]:
    """Lê email/senha da Alura do .env. Vazios se não definidos."""
    return (
        os.getenv("ALURA_EMAIL", ""),
        os.getenv("ALURA_PASSWORD", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Carregamento do .env
# ═══════════════════════════════════════════════════════════════════════════


def load_config() -> None:
    """Carrega `.env` e atualiza globais (LANG_PRIORITY)."""
    global LANG_PRIORITY
    load_dotenv()
    LANG_PRIORITY = get_lang_priority()


def resolve_cookies(cli_cookie: str | None = None) -> str | None:
    """Resolve cookies da Udemy: CLI > .env UDEMY_COOKIES > .env UDEMY_ACCESS_TOKEN.

    Inclui fallback de leitura direta do .env para casos onde o python-dotenv
    não consegue parsear aspas internas (cookies da Udemy têm muitas aspas).
    """
    if cli_cookie:
        return cli_cookie

    cookie_data = os.getenv("UDEMY_COOKIES") or os.getenv("UDEMY_ACCESS_TOKEN")

    if not cookie_data or (";" not in cookie_data and len(cookie_data) < 50):
        fallback = (
            _read_env_raw("UDEMY_COOKIES")
            or _read_env_raw("UDEMY_ACCESS_TOKEN")
        )
        if fallback and len(fallback) > len(cookie_data or ""):
            cookie_data = fallback

    return cookie_data


def _read_env_raw(key: str) -> str | None:
    """Lê um valor do .env sem depender do python-dotenv.

    Útil quando o valor contém aspas internas que confundem o parser
    (ex: access_token="abc..." dentro de aspas duplas).
    """
    env_path = Path(".env")
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            v = v.strip()
            if (v.startswith("'") and v.endswith("'")) or (
                v.startswith('"') and v.endswith('"')
            ):
                v = v[1:-1]
            return v

    return None
