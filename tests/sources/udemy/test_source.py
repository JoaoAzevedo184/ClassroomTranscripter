"""Testes do `UdemySource` — usa mocks pra simular client + HTTP."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.core.exceptions import (
    AuthenticationError,
    CourseNotFoundError,
    ParseError,
    TranscriptNotAvailableError,
)
from classroom_transcripter.core.models import Caption, Lecture, Module
from classroom_transcripter.sources.udemy import UdemySource


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def source() -> UdemySource:
    """Source com UdemyClient mockado pra evitar chamadas HTTP reais."""
    s = UdemySource(cookie="access_token=fake;cf_clearance=x", language="pt")
    s._client = MagicMock()
    return s


@pytest.fixture
def lecture_with_captions() -> Lecture:
    return Lecture(
        id=42,
        title="Intro",
        object_index=1,
        captions=[
            Caption(locale="en", url="https://cdn/en.vtt", label="English"),
            Caption(locale="pt", url="https://cdn/pt.vtt", label="Português"),
        ],
    )


# ─── Construtor + metadados ───────────────────────────────────────────────


def test_source_name_is_udemy():
    s = UdemySource(cookie="x")
    assert s.name == "udemy"


def test_source_stores_language_default():
    s = UdemySource(cookie="x")
    assert s.language == "pt"


def test_source_stores_custom_language():
    s = UdemySource(cookie="x", language="en")
    assert s.language == "en"


def test_client_is_lazy():
    """Construtor não deve instanciar UdemyClient (evita I/O/parsing do cookie no import)."""
    s = UdemySource(cookie="x")
    assert s._client is None


def test_repr_mentions_udemy():
    assert "UdemySource" in repr(UdemySource(cookie="x"))


# ─── authenticate ─────────────────────────────────────────────────────────


def test_authenticate_calls_users_me(source):
    source.authenticate()
    assert source._client._get.called
    called_url = source._client._get.call_args[0][0]
    assert "/users/me" in called_url


def test_authenticate_raises_on_auth_error(source):
    source._client._get.side_effect = AuthenticationError()
    with pytest.raises(AuthenticationError):
        source.authenticate()


def test_authenticate_wraps_other_errors(source):
    source._client._get.side_effect = ConnectionError("rede caiu")
    with pytest.raises(AuthenticationError, match="rede caiu"):
        source.authenticate()


# ─── fetch_course ─────────────────────────────────────────────────────────


def test_fetch_course_accepts_url(source):
    source._client.get_course_info.return_value = (123, "Docker Básico")
    source._client.get_curriculum.return_value = [Module(title="M1", index=1)]

    course = source.fetch_course("https://www.udemy.com/course/docker-basico/")

    # Slug foi extraído corretamente da URL
    source._client.get_course_info.assert_called_once_with("docker-basico")
    assert course.slug == "docker-basico"
    assert course.platform == "udemy"
    assert course.id == 123
    assert course.title == "Docker Básico"


def test_fetch_course_accepts_plain_slug(source):
    source._client.get_course_info.return_value = (1, "X")
    source._client.get_curriculum.return_value = []

    course = source.fetch_course("meu-curso-slug")
    source._client.get_course_info.assert_called_once_with("meu-curso-slug")
    assert course.slug == "meu-curso-slug"


def test_fetch_course_populates_modules(source):
    mods = [
        Module(title="Fundamentos", index=1, lectures=[
            Lecture(id=1, title="A", object_index=1),
        ]),
        Module(title="Avançado", index=2, lectures=[
            Lecture(id=2, title="B", object_index=1),
        ]),
    ]
    source._client.get_course_info.return_value = (7, "Curso")
    source._client.get_curriculum.return_value = mods

    course = source.fetch_course("curso")
    assert len(course.modules) == 2
    assert course.modules[0].title == "Fundamentos"
    assert list(course.iter_lectures())[1].id == 2


def test_fetch_course_unknown_slug_raises(source):
    source._client.get_course_info.side_effect = RuntimeError("HTTP 404")
    with pytest.raises(CourseNotFoundError):
        source.fetch_course("inexistente")


# ─── fetch_transcript ─────────────────────────────────────────────────────


def _vtt_sample() -> str:
    return (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.000\n"
        "Olá\n\n"
        "00:00:03.500 --> 00:00:05.000\n"
        "Tudo bem?\n"
    )


@patch("classroom_transcripter.sources.udemy.source.requests.get")
def test_fetch_transcript_prefers_matching_language(mock_get, source, lecture_with_captions):
    mock_get.return_value = MagicMock(text=_vtt_sample(), status_code=200)
    mock_get.return_value.raise_for_status = lambda: None

    t = source.fetch_transcript(lecture_with_captions)

    # Preferência de idioma: pt foi escolhida (não en)
    called_url = mock_get.call_args[0][0]
    assert "pt.vtt" in called_url
    assert t.language == "pt"
    assert t.lecture_id == 42
    assert t.has_timestamps


@patch("classroom_transcripter.sources.udemy.source.requests.get")
def test_fetch_transcript_populates_plain_text(mock_get, source, lecture_with_captions):
    mock_get.return_value = MagicMock(text=_vtt_sample(), status_code=200)
    mock_get.return_value.raise_for_status = lambda: None

    t = source.fetch_transcript(lecture_with_captions)
    assert "Olá" in t.plain_text
    assert "Tudo bem" in t.plain_text


def test_fetch_transcript_raises_when_no_captions(source):
    lecture = Lecture(id=1, title="X", object_index=1, captions=[])
    with pytest.raises(TranscriptNotAvailableError):
        source.fetch_transcript(lecture)


@patch("classroom_transcripter.sources.udemy.source.requests.get")
def test_fetch_transcript_raises_on_invalid_vtt(mock_get, source, lecture_with_captions):
    # Simula VTT malformado — `vtt_to_transcript` retorna plano vazio, não lança;
    # mas se ocorresse exceção, viraria ParseError.
    # Aqui testamos o caso onde o HTTP retorna algo que quebra o parser real:
    # simulamos diretamente uma exceção no parse via patch.
    mock_get.return_value = MagicMock(text="bom dia", status_code=200)
    mock_get.return_value.raise_for_status = lambda: None

    with patch("classroom_transcripter.sources.udemy.source.vtt_to_transcript",
               side_effect=ValueError("boom")):
        with pytest.raises(ParseError):
            source.fetch_transcript(lecture_with_captions)


# ─── list_available_languages ─────────────────────────────────────────────


def test_list_languages_returns_locales(source, lecture_with_captions):
    assert source.list_available_languages(lecture_with_captions) == ["en", "pt"]


def test_list_languages_empty_when_no_captions(source):
    lec = Lecture(id=1, title="X", object_index=1)
    assert source.list_available_languages(lec) == []
