"""Testes do `UdemyClient` focados em parsing e helpers estáticos (sem HTTP)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from classroom_transcripter.sources.udemy.client import UdemyClient


# ─── _extract_cookie_value ────────────────────────────────────────────────


def test_extract_cookie_value_simple():
    s = "access_token=abc; cf_clearance=xyz; other=1"
    assert UdemyClient._extract_cookie_value(s, "access_token") == "abc"
    assert UdemyClient._extract_cookie_value(s, "cf_clearance") == "xyz"


def test_extract_cookie_value_strips_quotes():
    s = 'access_token="quoted-value"; other=1'
    assert UdemyClient._extract_cookie_value(s, "access_token") == "quoted-value"


def test_extract_cookie_value_missing():
    assert UdemyClient._extract_cookie_value("other=1", "access_token") is None


def test_extract_cookie_value_handles_spaces():
    assert UdemyClient._extract_cookie_value("  access_token=abc  ; x=1", "access_token") == "abc"


# ─── _parse_lecture ───────────────────────────────────────────────────────


def test_parse_lecture_basic():
    item = {
        "id": 123,
        "title": "Introdução ao Docker",
        "object_index": 1,
        "asset": {"captions": []},
    }
    lec = UdemyClient._parse_lecture(item)
    assert lec.id == 123
    assert lec.title == "Introdução ao Docker"
    assert lec.object_index == 1
    assert lec.captions == []


def test_parse_lecture_with_captions():
    item = {
        "id": 1,
        "title": "X",
        "object_index": 1,
        "asset": {
            "captions": [
                {"locale_id": "pt", "url": "https://cdn/pt.vtt", "title": "Português"},
                {"locale_id": "en", "url": "https://cdn/en.vtt", "title": "English"},
            ]
        },
    }
    lec = UdemyClient._parse_lecture(item)
    assert len(lec.captions) == 2
    assert lec.captions[0].locale == "pt"
    assert lec.captions[0].url == "https://cdn/pt.vtt"


def test_parse_lecture_caption_fallback_label():
    """Se 'title' estiver ausente na caption, usa locale_id como label."""
    item = {
        "id": 1, "title": "X", "object_index": 1,
        "asset": {"captions": [{"locale_id": "pt-BR", "url": "u"}]},
    }
    lec = UdemyClient._parse_lecture(item)
    assert lec.captions[0].label == "pt-BR"


def test_parse_lecture_missing_title_falls_back():
    item = {"id": 1, "object_index": 1, "asset": {"captions": []}}
    lec = UdemyClient._parse_lecture(item)
    assert lec.title == "Sem título"


# ─── _setup_auth (sem HTTP real) ──────────────────────────────────────────


@pytest.fixture
def mock_session():
    """Mocka curl_cffi.requests.Session pra evitar I/O no __init__."""
    with patch("classroom_transcripter.sources.udemy.client.cffi_requests.Session") as m:
        yield m


def test_setup_auth_with_full_cookie_string(mock_session):
    """Cookie completa (com ;) → extrai access_token e monta Authorization."""
    UdemyClient("access_token=abc123; cf_clearance=xyz; expires=1h")
    instance = mock_session.return_value
    assert instance.headers.update.called
    headers = instance.headers.update.call_args[0][0]
    assert headers["Authorization"] == "Bearer abc123"
    assert headers["X-Udemy-Authorization"] == "Bearer abc123"
    assert "access_token=abc123" in headers["Cookie"]


def test_setup_auth_with_plain_token(mock_session):
    """Token simples (sem ;) → cookie = access_token=<token>."""
    UdemyClient("simpletoken123")
    instance = mock_session.return_value
    headers = instance.headers.update.call_args[0][0]
    assert headers["Authorization"] == "Bearer simpletoken123"
    assert headers["Cookie"] == "access_token=simpletoken123"


def test_setup_auth_strips_cookie_prefix(mock_session):
    """Se o usuário colou 'Cookie: ...' o prefixo é removido."""
    UdemyClient("Cookie: access_token=abc; x=1")
    instance = mock_session.return_value
    headers = instance.headers.update.call_args[0][0]
    assert headers["Authorization"] == "Bearer abc"


def test_setup_auth_removes_non_ascii(mock_session):
    """Chars … U+2026 (truncamento do terminal) são removidos pra curl_cffi aceitar."""
    UdemyClient("access_token=abc…; cf_clearance=xyz")
    instance = mock_session.return_value
    headers = instance.headers.update.call_args[0][0]
    # access_token ainda vale pq … foi removido mas abc sobrou
    assert "abc" in headers["Authorization"]


def test_setup_auth_exits_on_missing_access_token(mock_session):
    """Cookie sem access_token → sys.exit(1) (comportamento v0.1 preservado)."""
    with pytest.raises(SystemExit) as exc:
        UdemyClient("random_cookie=x; another=y")
    assert exc.value.code == 1
