"""Formatter texto puro.

MIGRAÇÃO (Fase 2):
-----------------
Extrair do atual `udemy_transcripter/formatters.py` só a parte do TxtFormatter.
Adaptar pra herdar de `BaseFormatter` e usar os modelos de `core.models`.
"""
from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.models import Course, Lecture, Transcript


class TxtFormatter(BaseFormatter):
    extension = ".txt"

    def format_lecture(
        self,
        lecture: Lecture,
        transcript: Transcript,
        *,
        include_timestamps: bool = False,
    ) -> str:
        # TODO Fase 2: migrar lógica do TxtFormatter atual
        raise NotImplementedError("Migrar de udemy_transcripter/formatters.py na Fase 2")

    def format_course_merged(
        self,
        course: Course,
        transcripts: dict[str, Transcript],
        *,
        include_timestamps: bool = False,
    ) -> str:
        raise NotImplementedError("Migrar de udemy_transcripter/formatters.py na Fase 2")
