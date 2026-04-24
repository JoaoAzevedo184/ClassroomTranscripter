"""`AluraSource`: `TranscriptSource` para Alura.

Implementado COMPLETO — delega pro `AluraClient` e `parser.py`.
Quando você preencher os TODOs em `client.py`, esta classe já funciona.
"""
from __future__ import annotations

from classroom_transcripter.core.exceptions import TranscriptNotAvailableError
from classroom_transcripter.core.models import Course, Lecture, Transcript
from classroom_transcripter.core.platforms import AluraPlatform
from classroom_transcripter.sources.alura.client import AluraClient
from classroom_transcripter.sources.alura.parser import parse_course, parse_transcript
from classroom_transcripter.sources.base import TranscriptSource


class AluraSource(TranscriptSource):
    """TranscriptSource pra Alura (email + senha)."""

    name = "alura"

    def __init__(
        self,
        email: str,
        password: str,
        *,
        language: str = "pt",
        debug: bool = False,
    ):
        """
        Args:
            email: email de login na Alura.
            password: senha.
            language: idioma default pro Transcript quando a API não retornar.
            debug: imprime detalhes das requisições.
        """
        self.email = email
        self.password = password
        self.language = language
        self.debug = debug
        self._client: AluraClient | None = None
        self._authenticated = False

    # ─── Cliente lazy ──────────────────────────────────────────────────

    @property
    def client(self) -> AluraClient:
        if self._client is None:
            self._client = AluraClient(self.email, self.password, debug=self.debug)
        return self._client

    # ─── API do TranscriptSource ──────────────────────────────────────

    def authenticate(self) -> None:
        """Faz login e guarda cookies de sessão no cliente."""
        self.client.login()
        self._authenticated = True

    def fetch_course(self, identifier: str) -> Course:
        """`identifier` = URL completa OU slug do curso Alura."""
        if not self._authenticated:
            self.authenticate()

        slug = AluraPlatform().extract_slug(identifier)
        raw = self.client.get_course(slug)
        return parse_course(raw, slug=slug)

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Busca transcrição de uma aula.

        A slug do curso precisa estar no metadata da Lecture — o parser poderia
        popular isso, mas como não sabemos o formato exato da API, depende de
        como você preencher o parse_course(). Alternativa: buscar via course_id
        se a API aceitar.
        """
        if not self._authenticated:
            self.authenticate()

        # O parser popula metadata com os dados que o client retornou.
        # Se a API da Alura usar course_slug + activity_id, populemos assim:
        course_slug = lecture.metadata.get("course_slug", "")
        if not course_slug:
            raise TranscriptNotAvailableError(
                f"Aula {lecture.id} não tem course_slug no metadata. "
                "Ajuste parse_course() em alura/parser.py pra populá-lo."
            )

        raw = self.client.get_transcript(course_slug, lecture.id)
        return parse_transcript(
            raw,
            lecture_id=lecture.id,
            default_language=self.language,
        )
