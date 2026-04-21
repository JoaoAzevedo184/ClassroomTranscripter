"""Interface base para formatadores de saída."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from classroom_transcripter.core.models import Lecture, Module
from classroom_transcripter.core.utils import sanitize_filename


class BaseFormatter(ABC):
    """Interface base para formatadores de saída.

    Trocas de vocabulário v0.1 → v0.2:
        Section → Module  (parâmetros renomeados)
        section → module
    """

    @abstractmethod
    def file_extension(self) -> str:
        """Extensão dos arquivos gerados (ex: '.txt', '.md')."""

    @abstractmethod
    def format_lecture(
        self,
        lecture: Lecture,
        module: Module,
        transcript: str,
        course_title: str,
        slug: str,
        prev_lecture: Lecture | None = None,
        next_lecture: Lecture | None = None,
    ) -> str:
        """Formata o conteúdo de uma aula individual."""

    @abstractmethod
    def format_merged(
        self,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        """Formata o arquivo mesclado com todo o curso."""

    def save_extras(
        self,
        course_dir: Path,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Hook pra salvar arquivos extras (MOC, índices, etc.). Default: no-op."""

    def get_lecture_filename(self, lecture: Lecture) -> str:
        name = f"{lecture.object_index:03d} - {sanitize_filename(lecture.title)}"
        return f"{name}{self.file_extension()}"

    def get_module_dirname(self, module: Module) -> str:
        return f"{module.index:02d} - {sanitize_filename(module.title)}"

    def get_merged_filename(self) -> str:
        return f"_CURSO_COMPLETO{self.file_extension()}"
