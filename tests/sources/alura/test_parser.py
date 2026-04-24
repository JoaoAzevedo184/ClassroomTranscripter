"""Testes do parser Alura — implementado por completo, testes reais."""
from __future__ import annotations

from classroom_transcripter.sources.alura.parser import (
    parse_course,
    parse_transcript,
)


# ─── parse_course ──────────────────────────────────────────────────────────


def test_parse_course_basic():
    raw = {
        "id": "curso-123",
        "title": "Docker Fundamentos",
        "sections": [
            {
                "id": "s1",
                "title": "Primeiros Passos",
                "index": 1,
                "activities": [
                    {"id": "a1", "title": "Instalação", "index": 1, "type": "video"},
                    {"id": "a2", "title": "Hello World", "index": 2, "type": "video"},
                ],
            },
            {
                "id": "s2",
                "title": "Imagens e Containers",
                "index": 2,
                "activities": [
                    {"id": "a3", "title": "Docker Run", "index": 1, "type": "video"},
                ],
            },
        ],
    }

    course = parse_course(raw, slug="docker-fundamentos")

    assert course.platform == "alura"
    assert course.slug == "docker-fundamentos"
    assert course.title == "Docker Fundamentos"
    assert len(course.modules) == 2
    assert course.modules[0].title == "Primeiros Passos"
    assert len(course.modules[0].lectures) == 2
    assert course.modules[0].lectures[0].title == "Instalação"
    assert course.modules[0].lectures[0].id == "a1"


def test_parse_course_empty_sections():
    course = parse_course({"id": "x", "title": "X", "sections": []}, slug="x")
    assert course.modules == []


def test_parse_course_missing_fields_fallback():
    """Campos ausentes recebem fallbacks razoáveis."""
    raw = {"sections": [{"activities": [{"id": 1}]}]}
    course = parse_course(raw, slug="x")
    assert course.id == "x"  # fallback pra slug
    assert course.title == "x"
    assert course.modules[0].lectures[0].title == "Sem título"


def test_parse_course_lecture_metadata_type():
    raw = {
        "title": "T", "sections": [{
            "title": "S", "index": 1, "activities": [
                {"id": 1, "title": "A", "index": 1, "type": "quiz"},
            ],
        }],
    }
    course = parse_course(raw, slug="x")
    assert course.modules[0].lectures[0].metadata["type"] == "quiz"


# ─── parse_transcript: formato A (segments) ──────────────────────────────


def test_parse_transcript_segments_format():
    raw = {
        "language": "pt",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Olá"},
            {"start": 2.5, "end": 5.0, "text": "mundo"},
        ],
    }
    t = parse_transcript(raw, lecture_id=1)
    assert t.has_timestamps
    assert len(t.cues) == 2
    assert t.cues[0].start_seconds == 0.0
    assert t.cues[0].text == "Olá"
    assert "Olá mundo" in t.plain_text
    assert t.language == "pt"


def test_parse_transcript_segments_default_language():
    raw = {"segments": [{"start": 0, "end": 1, "text": "x"}]}
    t = parse_transcript(raw, lecture_id=1, default_language="en")
    assert t.language == "en"


# ─── parse_transcript: formato B (texto corrido) ─────────────────────────


def test_parse_transcript_plain_text():
    raw = {"language": "pt", "transcript": "Olá pessoal, bem-vindos ao curso."}
    t = parse_transcript(raw, lecture_id=1)
    assert not t.has_timestamps
    assert t.plain_text == "Olá pessoal, bem-vindos ao curso."
    assert t.language == "pt"


def test_parse_transcript_text_alternative_key():
    """Aceita 'text' como alternativa a 'transcript'."""
    raw = {"text": "conteúdo direto"}
    t = parse_transcript(raw, lecture_id=1)
    assert t.plain_text == "conteúdo direto"


def test_parse_transcript_empty_fallback():
    t = parse_transcript({}, lecture_id=1)
    assert t.plain_text == ""
    assert t.cues == []


# ─── parse_transcript: formato C (VTT) ───────────────────────────────────


def test_parse_transcript_vtt_format():
    vtt_content = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.000\n"
        "Olá pessoal\n\n"
        "00:00:03.500 --> 00:00:06.000\n"
        "Bem-vindos\n"
    )
    raw = {"format": "vtt", "content": vtt_content, "language": "pt"}
    t = parse_transcript(raw, lecture_id=42)

    assert t.lecture_id == 42
    assert t.has_timestamps
    assert len(t.cues) == 2
    assert t.cues[0].start_seconds == 1.0
    assert t.cues[0].text == "Olá pessoal"
