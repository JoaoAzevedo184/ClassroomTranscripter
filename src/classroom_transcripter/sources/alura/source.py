"""AluraSource: implementação de `TranscriptSource` para Alura."""
from __future__ import annotations

from classroom_transcripter.core.models import Course, Lecture, Transcript
from classroom_transcripter.sources.base import TranscriptSource


class AluraSource(TranscriptSource):
    name = "alura"

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        # self._client = AluraClient()

    def authenticate(self) -> None:
        """Faz login e guarda cookies de sessão."""
        raise NotImplementedError("Implementar na Fase 7")

    def fetch_course(self, identifier: str) -> Course:
        """`identifier` = URL ou slug do curso Alura."""
        raise NotImplementedError("Implementar na Fase 7")

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Puxa o transcript oficial da aula (texto ou VTT, depende da Alura)."""
        raise NotImplementedError("Implementar na Fase 7")
