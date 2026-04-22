"""Testes do wrapper Whisper — só conversão e erros (sem cache em disco)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.core.exceptions import (
    ParseError,
    TranscriptNotAvailableError,
)
from classroom_transcripter.sources.dio.whisper_engine import (
    _transcript_from_whisper_result,
    transcribe,
)


FAKE_WHISPER_RESULT = {
    "text": "Olá pessoal, bem-vindos.",
    "language": "pt",
    "segments": [
        {"start": 0.0, "end": 2.5, "text": "Olá pessoal,"},
        {"start": 2.5, "end": 5.0, "text": " bem-vindos."},
    ],
}


def _fake_model():
    m = MagicMock()
    m.transcribe.return_value = FAKE_WHISPER_RESULT
    return m


# ─── Conversão pura ────────────────────────────────────────────────────────


def test_transcript_from_whisper_result_populates_cues():
    t = _transcript_from_whisper_result(FAKE_WHISPER_RESULT, lecture_id=1, language="pt")
    assert len(t.cues) == 2
    assert t.cues[0].start_seconds == 0.0
    assert t.cues[0].end_seconds == 2.5
    assert t.cues[0].text == "Olá pessoal,"
    assert t.has_timestamps


def test_transcript_from_whisper_result_plain_text():
    t = _transcript_from_whisper_result(FAKE_WHISPER_RESULT, lecture_id=1, language="pt")
    assert t.plain_text == "Olá pessoal, bem-vindos."
    assert t.language == "pt"


def test_transcript_strips_whitespace():
    result = {
        "text": " olá ",
        "language": "pt",
        "segments": [{"start": 0.0, "end": 1.0, "text": "   hello   "}],
    }
    t = _transcript_from_whisper_result(result, lecture_id=1, language="pt")
    assert t.plain_text == "olá"
    assert t.cues[0].text == "hello"


def test_transcript_empty_segments():
    """Sem segments, cues fica vazio mas plain_text ainda preenche."""
    result = {"text": "texto direto", "language": "pt", "segments": []}
    t = _transcript_from_whisper_result(result, lecture_id=1, language="pt")
    assert t.plain_text == "texto direto"
    assert t.cues == []
    assert not t.has_timestamps


# ─── transcribe() — chamadas reais com modelo mockado ─────────────────────


def test_transcribe_invokes_model(tmp_path):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"fake")

    fake = _fake_model()
    with patch(
        "classroom_transcripter.sources.dio.whisper_engine._load_model",
        return_value=fake,
    ):
        result = transcribe(video, lecture_id=42, model_name="small", language="pt")

    assert fake.transcribe.called
    assert result.lecture_id == 42
    assert result.plain_text == "Olá pessoal, bem-vindos."


def test_transcribe_passes_model_name(tmp_path):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"fake")

    with patch(
        "classroom_transcripter.sources.dio.whisper_engine._load_model",
        return_value=_fake_model(),
    ) as mock_load:
        transcribe(video, lecture_id=1, model_name="medium")

    mock_load.assert_called_with("medium")


def test_transcribe_passes_language_to_model(tmp_path):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"fake")
    fake = _fake_model()

    with patch(
        "classroom_transcripter.sources.dio.whisper_engine._load_model",
        return_value=fake,
    ):
        transcribe(video, lecture_id=1, language="en")

    kwargs = fake.transcribe.call_args.kwargs
    assert kwargs["language"] == "en"


# ─── Errors ────────────────────────────────────────────────────────────────


def test_missing_file_raises(tmp_path):
    with pytest.raises(TranscriptNotAvailableError, match="não encontrado"):
        transcribe(tmp_path / "nao-existe.mp4", lecture_id=1)


def test_whisper_exception_becomes_parse_error(tmp_path):
    video = tmp_path / "a.mp4"
    video.write_bytes(b"x")

    bad_model = MagicMock()
    bad_model.transcribe.side_effect = RuntimeError("GPU out of memory")

    with patch(
        "classroom_transcripter.sources.dio.whisper_engine._load_model",
        return_value=bad_model,
    ):
        with pytest.raises(ParseError, match="GPU out of memory"):
            transcribe(video, lecture_id=1)


def test_malformed_whisper_result_raises_parse_error(tmp_path):
    """Se Whisper retornar estrutura inesperada, vira ParseError."""
    video = tmp_path / "a.mp4"
    video.write_bytes(b"x")

    weird_model = MagicMock()
    weird_model.transcribe.return_value = {"segments": [{"no_start_field": True}]}

    with patch(
        "classroom_transcripter.sources.dio.whisper_engine._load_model",
        return_value=weird_model,
    ):
        with pytest.raises(ParseError):
            transcribe(video, lecture_id=1)
