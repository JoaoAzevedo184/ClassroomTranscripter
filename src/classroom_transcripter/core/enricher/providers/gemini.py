"""Provider Gemini.

MIGRAÇÃO (Fase 2):
-----------------
Extrair do atual `udemy_transcripter/enricher.py` a classe/função que chama Gemini.
Adaptar pra herdar de `AIProvider` e lançar `ProviderError` em falhas.

Import da lib externa fica no topo deste arquivo — o `__init__.py` do enricher
importa tardiamente via factory, então só quem usa Gemini precisa ter a lib instalada.
"""
from classroom_transcripter.core.enricher.base import AIProvider


class GeminiProvider(AIProvider):
    name = "gemini"
    # default_model = "..."  # TODO Fase 2

    def __init__(self, **kwargs):
        # TODO Fase 2: migrar __init__ do enricher atual
        raise NotImplementedError("Migrar na Fase 2")

    def complete(self, system_prompt: str, user_content: str, *, model: str | None = None) -> str:
        raise NotImplementedError("Migrar na Fase 2")
