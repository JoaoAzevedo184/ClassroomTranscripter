"""Wrapper do OpenAI Whisper pra transcrição local.

Sem cache em disco — o `--resume` do downloader já cobre o caso de retomar
depois de uma interrupção (se o arquivo .md foi gerado, pula).

O modelo Whisper é carregado LAZILY e CACHEADO EM MEMÓRIA via `lru_cache`.
Isso é diferente do cache em disco: só evita pagar o load (~500MB pra 'small')
várias vezes na MESMA execução. Entre execuções, o modelo é recarregado
(mas os pesos já baixados ficam no cache padrão do whisper em `~/.cache/whisper`).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from classroom_transcripter.core.exceptions import (
    ParseError,
    TranscriptNotAvailableError,
)
from classroom_transcripter.core.models import Transcript, TranscriptCue


# ─── Modelo (lazy + cached em memória durante a execução) ──────────────────


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    """Carrega modelo Whisper. LRU pra reusar entre chamadas do mesmo run."""
    try:
        import whisper  # type: ignore[import-untyped]
    except ImportError as e:
        raise TranscriptNotAvailableError(
            "Whisper não instalado. Instale com: pip install 'classroom-transcripter[dio]'"
        ) from e
    return whisper.load_model(model_name)


# ─── API pública ────────────────────────────────────────────────────────────


def transcribe(
    media_path: Path,
    *,
    lecture_id: int | str,
    model_name: str = "small",
    language: str = "pt",
) -> Transcript:
    """Transcreve um arquivo de áudio/vídeo com Whisper.

    Args:
        media_path: .mp4/.mkv/.mp3/etc.
        lecture_id: ID da Lecture (populado no Transcript retornado).
        model_name: tiny | base | small | medium | large.
        language: código ISO do idioma falado ('pt', 'en', etc).

    Returns:
        Transcript com cues (segmentos do Whisper viram TranscriptCues).

    Raises:
        TranscriptNotAvailableError: arquivo não existe ou lib Whisper ausente.
        ParseError: Whisper retornou estrutura inesperada.
    """
    media_path = Path(media_path).expanduser()
    if not media_path.exists():
        raise TranscriptNotAvailableError(
            f"Arquivo de mídia não encontrado: {media_path}"
        )

    model = _load_model(model_name)
    try:
        result = model.transcribe(
            str(media_path),
            language=language,
            verbose=False,
        )
    except Exception as e:
        raise ParseError(f"Whisper falhou em {media_path.name}: {e}") from e

    try:
        return _transcript_from_whisper_result(result, lecture_id, language)
    except (KeyError, TypeError) as e:
        raise ParseError(f"Formato inesperado do Whisper: {e}") from e


# ─── Internos ───────────────────────────────────────────────────────────────


def _transcript_from_whisper_result(
    result: dict,
    lecture_id: int | str,
    language: str,
) -> Transcript:
    """Converte o dict retornado por `whisper.transcribe()` num `Transcript`."""
    cues = [
        TranscriptCue(
            start_seconds=float(seg["start"]),
            end_seconds=float(seg["end"]),
            text=str(seg["text"]).strip(),
        )
        for seg in result.get("segments", [])
    ]
    return Transcript(
        lecture_id=lecture_id,
        language=result.get("language", language),
        cues=cues,
        plain_text=str(result.get("text", "")).strip(),
    )
