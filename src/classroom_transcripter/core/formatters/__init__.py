"""Formatadores de saída.

Cada formatter recebe um Transcript/Lecture/Course e gera arquivos.
Formatadores são plataforma-agnósticos: Obsidian funciona igual pra
transcript vindo de Udemy, DIO ou Alura.
"""
from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.formatters.obsidian import ObsidianFormatter
from classroom_transcripter.core.formatters.txt import TxtFormatter

__all__ = ["BaseFormatter", "ObsidianFormatter", "TxtFormatter"]


def get_formatter(name: str) -> BaseFormatter:
    """Factory simples por nome: 'txt' | 'obsidian'."""
    formatters = {
        "txt": TxtFormatter,
        "obsidian": ObsidianFormatter,
    }
    if name not in formatters:
        raise ValueError(f"Formatter desconhecido: {name!r}. Opções: {list(formatters)}")
    return formatters[name]()
