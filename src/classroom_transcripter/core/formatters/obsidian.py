"""Formatter Obsidian (Markdown com frontmatter + wikilinks + callouts).

MIGRAÇÃO (Fase 2):
-----------------
Extrair do atual `udemy_transcripter/formatters.py` a parte do ObsidianFormatter.
Adaptar pra herdar de `BaseFormatter` e usar `core.models`.

CONSIDERAR (novo):
- Campo frontmatter `platform: udemy | dio | alura` pra permitir filtros no Obsidian.
- Campo `source_url` só quando existir (DIO pode não ter).
"""
from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.models import Course, Lecture, Transcript


class ObsidianFormatter(BaseFormatter):
    extension = ".md"

    def format_lecture(
        self,
        lecture: Lecture,
        transcript: Transcript,
        *,
        include_timestamps: bool = False,
    ) -> str:
        # TODO Fase 2: migrar lógica e ADICIONAR frontmatter `platform`
        raise NotImplementedError("Migrar de udemy_transcripter/formatters.py na Fase 2")

    def format_course_merged(
        self,
        course: Course,
        transcripts: dict[str, Transcript],
        *,
        include_timestamps: bool = False,
    ) -> str:
        raise NotImplementedError("Migrar de udemy_transcripter/formatters.py na Fase 2")
