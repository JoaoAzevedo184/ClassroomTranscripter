"""Contrato base de um formatador de saída."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from classroom_transcripter.core.models import Course, Lecture, Transcript


class BaseFormatter(ABC):
    """Todo formatter converte (Lecture + Transcript) em um arquivo no disco.

    Pode também gerar um arquivo "merged" (curso inteiro em um doc).
    """

    #: extensão incluindo ponto, ex: ".md", ".txt"
    extension: str = ""

    @abstractmethod
    def format_lecture(
        self,
        lecture: Lecture,
        transcript: Transcript,
        *,
        include_timestamps: bool = False,
    ) -> str:
        """Devolve o conteúdo textual de UMA aula formatada."""

    @abstractmethod
    def format_course_merged(
        self,
        course: Course,
        transcripts: dict[str, Transcript],
        *,
        include_timestamps: bool = False,
    ) -> str:
        """Devolve o curso inteiro em um único documento (feature `--merge`)."""

    def write_lecture(
        self,
        lecture: Lecture,
        transcript: Transcript,
        output_path: Path,
        *,
        include_timestamps: bool = False,
    ) -> Path:
        """Helper padrão: chama format_lecture e grava no disco."""
        content = self.format_lecture(lecture, transcript, include_timestamps=include_timestamps)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
