"""Modelos de domínio — agnósticos de plataforma.

Hierarquia:
    Course  ⊃  Module  ⊃  Lecture  ⊃  Caption[]
    Transcript  ⊃  TranscriptCue[]

Filosofia dos nomes (purista, v0.2):
    Section → Module      (vocabulário mais universal entre plataformas)
    (novo) → Course       (adiciona contexto do curso inteiro)
    (novo) → Transcript   (encapsula texto + timestamps — útil pro Whisper da DIO)
    (novo) → TranscriptCue (trecho com timestamp)

Compatibilidade com v0.1: NÃO mantida intencionalmente. Código que importava
`Section` (agora `Module`) precisa ser atualizado junto.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


# ─── Captions / transcrições ────────────────────────────────────────────────


@dataclass
class Caption:
    """Legenda de uma aula (Udemy, Alura). Ponteiro pra um arquivo VTT remoto."""

    locale: str
    url: str
    label: str


@dataclass
class TranscriptCue:
    """Trecho de transcrição com timestamp (usado pelo Whisper da DIO e VTTs)."""

    start_seconds: float
    end_seconds: float
    text: str


@dataclass
class Transcript:
    """Transcrição completa de uma aula, com ou sem timestamps.

    Quando vem do Whisper (DIO) → `cues` preenchido.
    Quando vem de VTT parseado (Udemy/Alura) → `cues` preenchido.
    Quando vem de scraping sem timestamps → só `plain_text`.
    """

    lecture_id: int | str
    language: str
    cues: list[TranscriptCue] = field(default_factory=list)
    plain_text: str = ""

    @property
    def has_timestamps(self) -> bool:
        return bool(self.cues)


# ─── Estrutura de cursos ────────────────────────────────────────────────────


@dataclass
class Lecture:
    """Aula individual (vídeo, artigo, desafio)."""

    id: int | str
    title: str
    object_index: int
    captions: list[Caption] = field(default_factory=list)
    # Metadados específicos por plataforma (DIO guarda path do .mp4 aqui)
    metadata: dict = field(default_factory=dict)


@dataclass
class Module:
    """Agrupamento de aulas (chapter na Udemy, módulo na DIO, etc.).

    Antes chamado de `Section` — renomeado na Fase 2 pra vocabulário universal.
    """

    title: str
    index: int
    lectures: list[Lecture] = field(default_factory=list)


@dataclass
class Course:
    """Curso/bootcamp/trilha completo."""

    id: int | str
    slug: str
    title: str
    platform: str  # "udemy" | "dio" | "alura"
    modules: list[Module] = field(default_factory=list)
    language: str | None = None
    instructor: str | None = None
    metadata: dict = field(default_factory=dict)

    def iter_lectures(self) -> Iterator[Lecture]:
        for module in self.modules:
            yield from module.lectures


# ─── Resultado de execução ──────────────────────────────────────────────────


@dataclass
class DownloadResult:
    """Estatísticas de um download/transcrição completo."""

    course_title: str
    course_id: int | str
    slug: str
    platform: str  # novo v0.2
    total_modules: int  # era total_sections
    total_lectures: int
    downloaded: int
    errors: int
    output_dir: str
    skipped: int = 0  # novo v0.2 — pro --resume
