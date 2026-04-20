"""DioSource: implementação de `TranscriptSource` para DIO.

Como DIO não expõe API de transcrição, a estratégia é:
1. Usuário baixa os .mp4 (manualmente ou via outra ferramenta) numa pasta.
2. DioSource varre a pasta (`video_finder`) e infere Course/Modules/Lectures.
3. `fetch_transcript` roda Whisper localmente no arquivo correspondente.
"""
from __future__ import annotations

from pathlib import Path

from classroom_transcripter.core.models import Course, Lecture, Transcript
from classroom_transcripter.sources.base import TranscriptSource


class DioSource(TranscriptSource):
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
                           Padrão 'small' = bom equilíbrio qualidade/velocidade.
            language: idioma das aulas pro Whisper.
        """
        self.whisper_model = whisper_model
        self.language = language

    def authenticate(self) -> None:
        """No-op: DIO só lê arquivos locais, não precisa de auth."""
        return None

    def fetch_course(self, identifier: str) -> Course:
        """`identifier` aqui é um PATH pra pasta do bootcamp baixado.

        Ex: '/home/joao/dio_videos/formacao-java-backend'
        """
        # from classroom_transcripter.sources.dio.video_finder import discover_course
        # return discover_course(Path(identifier))
        raise NotImplementedError("Implementar na Fase 6")

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Roda Whisper no .mp4 que está em lecture.metadata['file']."""
        # from classroom_transcripter.sources.dio.whisper_engine import transcribe
        # media = Path(lecture.metadata["file"])
        # return transcribe(media, lecture_id=lecture.id,
        #                   model_name=self.whisper_model, language=self.language)
        raise NotImplementedError("Implementar na Fase 6")
