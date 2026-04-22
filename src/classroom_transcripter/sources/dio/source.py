"""`DioSource`: `TranscriptSource` baseado em Whisper local.

Fluxo (diferente de Udemy/Alura):
    1. Usuário baixa .mp4 do DIO manualmente (ou via outra ferramenta).
    2. Organiza em subpastas por módulo (convenção obrigatória).
    3. `fetch_course(path)` descobre a estrutura via `video_finder`.
    4. `fetch_transcript(lecture)` roda Whisper no arquivo que tá em
       `lecture.metadata["file"]` (populado pelo video_finder).

Como é 100% local, `authenticate()` é no-op.
Pra retomar um download interrompido, use `--resume` do downloader genérico.
"""
from __future__ import annotations

from pathlib import Path

from classroom_transcripter.core.models import Course, Lecture, Transcript
from classroom_transcripter.sources.base import TranscriptSource
from classroom_transcripter.sources.dio.video_finder import discover_course
from classroom_transcripter.sources.dio.whisper_engine import transcribe


class DioSource(TranscriptSource):
    """TranscriptSource pra DIO — Whisper local sobre .mp4 baixados."""

    name = "dio"

    def __init__(
        self,
        *,
        whisper_model: str = "small",
        language: str = "pt",
    ):
        """
        Args:
            whisper_model: tiny | base | small | medium | large.
                           'small' é o melhor equilíbrio qualidade/velocidade
                           no hardware típico de homelab.
            language: código ISO do idioma falado nas aulas.
        """
        self.whisper_model = whisper_model
        self.language = language

    def authenticate(self) -> None:
        """No-op: DIO só lê arquivos locais, não tem auth."""
        return None

    def fetch_course(self, identifier: str) -> Course:
        """`identifier` é o path pra pasta do bootcamp baixado.

        A pasta DEVE ter subpastas (uma por módulo). Ver `video_finder` pra
        detalhes da convenção.
        """
        return discover_course(Path(identifier))

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Roda Whisper no arquivo em `lecture.metadata['file']`."""
        media_path = Path(lecture.metadata["file"])
        return transcribe(
            media_path,
            lecture_id=lecture.id,
            model_name=self.whisper_model,
            language=self.language,
        )
