"""Formatter de texto puro (.txt) — v0.1 comportamento preservado."""
from __future__ import annotations

from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.models import Lecture, Module


class PlainTextFormatter(BaseFormatter):
    """Texto simples. Ideal pra pipeline de IA ou colar em outras ferramentas."""

    def file_extension(self) -> str:
        return ".txt"

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
        return transcript

    def format_merged(
        self,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        parts = [
            f"Curso: {course_title}",
            f"Total de aulas transcritas: {total_downloaded}",
            "=" * 60,
        ]

        for module in modules:
            module_lectures = [lec for lec in module.lectures if lec.id in transcripts]
            if not module_lectures:
                continue

            parts.append(f"\n{'=' * 60}")
            parts.append(f"SEÇÃO: {module.title}")
            parts.append(f"{'=' * 60}\n")

            for lecture in module_lectures:
                parts.append(f"\n--- {lecture.title} ---\n")
                parts.append(transcripts[lecture.id])
                parts.append("")

        return "\n".join(parts)
