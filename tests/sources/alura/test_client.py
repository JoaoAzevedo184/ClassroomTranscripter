"""Testes do AluraClient — sem rodar os TODOs.

Os 3 métodos principais (login, get_course, get_transcript) são NotImplementedError
por design. Este arquivo testa o wrapper e o resto da classe.
"""
from __future__ import annotations

import pytest

from classroom_transcripter.sources.alura.client import BASE_URL, AluraClient


def test_base_url_is_alura():
    assert "cursos.alura.com.br" in BASE_URL


def test_client_stores_credentials():
    c = AluraClient("e@x.com", "secret")
    assert c.email == "e@x.com"
    assert c.password == "secret"
    c.close()


def test_client_creates_http_session():
    """A sessão httpx é criada e configurada com base_url correto."""
    c = AluraClient("e", "s")
    assert c.session is not None
    assert str(c.session.base_url).startswith("https://cursos.alura.com.br")
    c.close()


def test_client_starts_not_logged_in():
    c = AluraClient("e", "s")
    assert c._logged_in is False
    c.close()


def test_client_is_context_manager():
    """Pode ser usado com `with`."""
    with AluraClient("e", "s") as c:
        assert c is not None
    # session foi fechada — usar novamente deve falhar
    # (não vamos testar o erro exato porque httpx pode variar entre versões)


def test_login_is_not_implemented():
    """TODO Fase 7.1 — garantir que está marcado como NotImplementedError."""
    with AluraClient("e", "s") as c:
        with pytest.raises(NotImplementedError, match="7.1"):
            c.login()


def test_get_course_is_not_implemented():
    """TODO Fase 7.2."""
    with AluraClient("e", "s") as c:
        with pytest.raises(NotImplementedError, match="7.2"):
            c.get_course("slug")


def test_get_transcript_is_not_implemented():
    """TODO Fase 7.3."""
    with AluraClient("e", "s") as c:
        with pytest.raises(NotImplementedError, match="7.3"):
            c.get_transcript("slug", "activity")
