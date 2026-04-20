"""Modelos de domínio compartilhados entre todas as plataformas.

Estas dataclasses são o "idioma comum" que todo `TranscriptSource` fala.
Se Udemy, DIO e Alura devolvem tipos diferentes internamente, cada source
é responsável por traduzir pra estes modelos aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TranscriptCue:
    """Um trecho com timestamp. Usado quando a fonte expõe tempo (VTT, Whisper segments)."""
    start_seconds: float
    end_seconds: float
    text: str


@dataclass
class Transcript:
    """Transcrição completa de uma aula, com ou sem timestamps."""
    lecture_id: str
    language: str  # "pt", "en", "es", ...
    cues: list[TranscriptCue] = field(default_factory=list)
    plain_text: str = ""  # quando a fonte só dá texto corrido (ex: scraping Alura)

    @property
    def has_timestamps(self) -> bool:
        return bool(self.cues)


@dataclass
class Lecture:
    """Uma aula individual. Pode ser vídeo, artigo, desafio, etc."""
    id: str
    title: str
    order: int  # posição dentro do módulo
    duration_seconds: int | None = None
    kind: str = "video"  # "video" | "article" | "quiz" | "challenge"
    source_url: str | None = None
    # Campo genérico pra cada source guardar metadados proprietários
    metadata: dict = field(default_factory=dict)


@dataclass
class Module:
    """Agrupamento de aulas (capítulo, seção, módulo — nomenclatura varia)."""
    id: str
    title: str
    order: int
    lectures: list[Lecture] = field(default_factory=list)


@dataclass
class Course:
    """Curso/bootcamp/trilha completo."""
    id: str
    slug: str
    title: str
    platform: str  # "udemy" | "dio" | "alura"
    modules: list[Module] = field(default_factory=list)
    language: str | None = None
    instructor: str | None = None
    metadata: dict = field(default_factory=dict)

    def iter_lectures(self):
        for m in self.modules:
            yield from m.lectures


@dataclass
class DownloadResult:
    """Resultado de uma operação de download/transcrição completa."""
    course: Course
    output_dir: Path
    files_created: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # lecture_ids que falharam/pularam
    errors: list[str] = field(default_factory=list)
