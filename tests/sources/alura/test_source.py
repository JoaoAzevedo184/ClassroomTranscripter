"""Testes do AluraSource — wiring (client mockado, TODOs não executados)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from classroom_transcripter.core.exceptions import TranscriptNotAvailableError
from classroom_transcripter.core.models import Lecture, Transcript
from classroom_transcripter.sources.alura import AluraSource


@pytest.fixture
def source() -> AluraSource:
    """AluraSource com AluraClient mockado — evita chamar os TODOs reais."""
    s = AluraSource(email="e@x.com", password="secret")
    s._client = MagicMock()
    return s


def test_source_name():
    assert AluraSource(email="x", password="y").name == "alura"


def test_client_is_lazy():
    """Construtor NÃO instancia cliente (evita TODOs travando testes)."""
    s = AluraSource(email="x", password="y")
    assert s._client is None


def test_authenticate_calls_client_login(source):
    source.authenticate()
    source._client.login.assert_called_once()
    assert source._authenticated is True


def test_fetch_course_authenticates_first(source):
    """fetch_course deve chamar login se ainda não autenticou."""
    source._client.get_course.return_value = {
        "id": "c1", "title": "Curso", "sections": [],
    }
    source.fetch_course("https://cursos.alura.com.br/course/docker")

    source._client.login.assert_called_once()
    source._client.get_course.assert_called_once_with("docker")


def test_fetch_course_skips_login_if_authenticated(source):
    source._authenticated = True
    source._client.get_course.return_value = {"id": "c", "title": "C", "sections": []}
    source.fetch_course("slug-direto")
    source._client.login.assert_not_called()


def test_fetch_course_extracts_slug_from_url(source):
    source._client.get_course.return_value = {"id": "c", "title": "C", "sections": []}
    source.fetch_course("https://cursos.alura.com.br/course/meu-slug?ref=x")
    source._client.get_course.assert_called_once_with("meu-slug")


def test_fetch_course_accepts_plain_slug(source):
    source._client.get_course.return_value = {"id": "c", "title": "C", "sections": []}
    source.fetch_course("plain-slug")
    source._client.get_course.assert_called_once_with("plain-slug")


def test_fetch_course_returns_parsed_course(source):
    source._client.get_course.return_value = {
        "id": "c", "title": "Meu Curso", "sections": [
            {"title": "M1", "index": 1, "activities": [
                {"id": "a1", "title": "A", "index": 1},
            ]},
        ],
    }
    course = source.fetch_course("slug")
    assert course.platform == "alura"
    assert course.title == "Meu Curso"
    assert len(course.modules) == 1
    assert course.modules[0].lectures[0].title == "A"


def test_fetch_transcript_without_course_slug_raises(source):
    """Lecture sem course_slug no metadata lança TranscriptNotAvailableError."""
    source._authenticated = True
    lec = Lecture(id=1, title="A", object_index=1, metadata={})

    with pytest.raises(TranscriptNotAvailableError, match="course_slug"):
        source.fetch_transcript(lec)


def test_fetch_transcript_happy_path(source):
    source._authenticated = True
    source._client.get_transcript.return_value = {
        "transcript": "texto da aula",
        "language": "pt",
    }
    lec = Lecture(
        id="a1", title="Aula", object_index=1,
        metadata={"course_slug": "meu-curso"},
    )

    t = source.fetch_transcript(lec)

    source._client.get_transcript.assert_called_once_with("meu-curso", "a1")
    assert isinstance(t, Transcript)
    assert t.plain_text == "texto da aula"
    assert t.lecture_id == "a1"


def test_fetch_transcript_vtt_format(source):
    source._authenticated = True
    source._client.get_transcript.return_value = {
        "format": "vtt",
        "content": (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:02.000\n"
            "olá\n"
        ),
    }
    lec = Lecture(id=1, title="A", object_index=1, metadata={"course_slug": "x"})

    t = source.fetch_transcript(lec)
    assert t.has_timestamps
    assert t.cues[0].text == "olá"
