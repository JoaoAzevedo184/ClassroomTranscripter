"""Formatadores de saída (plataforma-agnósticos)."""
from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.formatters.obsidian import ObsidianFormatter
from classroom_transcripter.core.formatters.txt import PlainTextFormatter

__all__ = [
    "BaseFormatter",
    "ObsidianFormatter",
    "PlainTextFormatter",
    "FORMATTERS",
    "get_formatter",
]


FORMATTERS: dict[str, type[BaseFormatter]] = {
    "txt": PlainTextFormatter,
    "obsidian": ObsidianFormatter,
}


def get_formatter(name: str, **kwargs) -> BaseFormatter:
    """Retorna uma instância do formatador pelo nome.

    Args:
        name: "txt" ou "obsidian".
        **kwargs: argumentos repassados ao construtor (ex: platform="dio"
                  pro ObsidianFormatter).

    Raises:
        ValueError: formatador não existe.
    """
    cls = FORMATTERS.get(name)
    if cls is None:
        available = ", ".join(FORMATTERS.keys())
        raise ValueError(
            f"Formatador '{name}' não encontrado. Disponíveis: {available}"
        )
    return cls(**kwargs)
