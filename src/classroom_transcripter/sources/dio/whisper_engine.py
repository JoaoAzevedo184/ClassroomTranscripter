"""Wrapper do OpenAI Whisper pra transcrição local.

MIGRAÇÃO (Fase 6):
-----------------
COPIAR código do teu repositório `whisper-transcriber` pra cá.
Adaptar a interface pra devolver um `Transcript` de `core.models`
(mapear os `segments` do Whisper → list[TranscriptCue]).

Funções principais esperadas:
- transcribe(audio_or_video_path: Path, *, model_name: str = "small",
             language: str = "pt") -> Transcript
- load_model(name: str) -> WhisperModel  (cached)

Considerações:
- Whisper retorna segmentos com start/end em segundos → perfeito pra TranscriptCue.
- Lazy import do `whisper` (dependência pesada, só carrega se DIO for usado).
- Modelo padrão: "small" (bom equilíbrio qualidade/velocidade no teu hardware i3+24GB).
- Suportar --model (tiny, base, small, medium, large) via CLI.
"""
from __future__ import annotations

from pathlib import Path

from classroom_transcripter.core.models import Transcript


def transcribe(
    media_path: Path,
    *,
    lecture_id: str,
    model_name: str = "small",
    language: str = "pt",
) -> Transcript:
    """TODO Fase 6: portar do repo whisper-transcriber."""
    raise NotImplementedError(
        "Fase 6: copiar whisper-transcriber pra cá e adaptar retorno pra Transcript."
    )
