"""Contrato base de uma fonte de transcrições.

ESTA É A PEÇA CENTRAL DA REFATORAÇÃO.

Toda plataforma (Udemy, DIO, Alura, futuras) implementa esta interface.
Quem consome um `TranscriptSource` (downloader, CLI, etc.) não precisa
saber se os dados vêm de API, scraping ou Whisper local.

Fluxo típico:
    source = UdemySource(cookie="...")
    source.authenticate()
    course = source.fetch_course("https://udemy.com/course/meu-curso/")
    for lecture in course.iter_lectures():
        transcript = source.fetch_transcript(lecture)
        # ... formata, salva, enriquece
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from classroom_transcripter.core.models import Course, Lecture, Transcript


class TranscriptSource(ABC):
    """Interface comum a todas as plataformas.

    Attributes:
        name: identificador curto e lowercase ('udemy' | 'dio' | 'alura').
              Usado em logs, paths de output e frontmatter do Obsidian.
    """

    name: str = ""

    # --- Autenticação ---

    @abstractmethod
    def authenticate(self) -> None:
        """Valida credenciais e prepara sessão/cliente para chamadas subsequentes.

        Deve levantar `AuthenticationError` se credenciais forem inválidas.
        Para DIO (que só usa arquivos locais), pode ser no-op.
        """

    # --- Descoberta de curso ---

    @abstractmethod
    def fetch_course(self, identifier: str) -> Course:
        """Resolve um identificador pra um Course populado com Modules e Lectures.

        Args:
            identifier: pode ser URL, slug, ou path local (no caso da DIO,
                        onde o "curso" é uma pasta com os .mp4 baixados).

        Levanta:
            CourseNotFoundError: identifier inválido.
            AccessDeniedError: usuário não tem acesso.
        """

    # --- Transcrição de aula individual ---

    @abstractmethod
    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Retorna o Transcript de UMA aula.

        Como cada source resolve isso:
          - Udemy: chama API de captions, parseia VTT
          - Alura: scraping do painel de transcript ou API
          - DIO: roda Whisper no .mp4 correspondente à aula

        Levanta:
            TranscriptNotAvailableError: aula sem transcript (ex: sem legendas).
        """

    # --- Helpers (têm implementação default) ---

    def iter_lectures(self, course: Course) -> Iterable[Lecture]:
        """Iterador plano de aulas em ordem de módulo → aula."""
        for module in course.modules:
            yield from module.lectures

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
