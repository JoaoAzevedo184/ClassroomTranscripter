"""UdemySource: implementação de `TranscriptSource` para Udemy.

MIGRAÇÃO (Fase 3):
-----------------
Esta classe é NOVA — ela envelopa a funcionalidade que hoje está espalhada
entre `client.py` e `downloader.py`. O objetivo é expor uma API uniforme
que conversa com o contrato `TranscriptSource`.

Lógica interna REAPROVEITA:
- `sources/udemy/client.py` (cliente HTTP)
- `sources/udemy/parser.py` (parsing API → Course)
- `core/vtt.py` (parsing VTT → TranscriptCue)
"""
from __future__ import annotations

from classroom_transcripter.core.models import Course, Lecture, Transcript
from classroom_transcripter.sources.base import TranscriptSource


class UdemySource(TranscriptSource):
    name = "udemy"

    def __init__(self, cookie: str, *, language: str = "pt"):
        """
        Args:
            cookie: string de cookies do navegador (access_token + cf_clearance + ...).
            language: código preferido de idioma pras captions ('pt', 'en', 'es', ...).
        """
        self.cookie = cookie
        self.language = language
        # self._client = UdemyClient(cookie)  # descomenta após migrar client.py
        # TODO Fase 3

    def authenticate(self) -> None:
        """Faz uma request leve (/users/me) pra validar que o cookie não expirou."""
        raise NotImplementedError("Implementar na Fase 3 após migrar client.py")

    def fetch_course(self, identifier: str) -> Course:
        """Aceita URL completa ou slug. Resolve slug e baixa curriculum."""
        raise NotImplementedError("Implementar na Fase 3")

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Busca captions da lecture e parseia VTT pra TranscriptCue."""
        raise NotImplementedError("Implementar na Fase 3")

    # --- Helpers específicos de Udemy ---

    def list_available_languages(self, lecture: Lecture) -> list[str]:
        """Devolve códigos de idioma disponíveis pras captions da aula (flag --list-langs)."""
        raise NotImplementedError("Implementar na Fase 3")
