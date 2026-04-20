"""Contrato base de um provider de IA para enriquecimento."""
from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Todo provider recebe um texto bruto e devolve texto enriquecido.

    "Enriquecido" = com formatação Obsidian: headings, callouts, destaques,
    possivelmente resumo no topo. O prompt fica em `core.enricher.pipeline`.
    """

    name: str = ""
    default_model: str = ""

    @abstractmethod
    def complete(self, system_prompt: str, user_content: str, *, model: str | None = None) -> str:
        """Chama o LLM e devolve a resposta como string.

        Deve levantar `ProviderError` (ou subclasse) em caso de falha.
        """
