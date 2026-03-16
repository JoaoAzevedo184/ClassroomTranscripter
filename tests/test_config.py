"""Testes de configuração e resolução de cookies."""

from pathlib import Path

from udemy_transcripter.config import _read_env_raw


def test_read_env_raw_single_quotes(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "UDEMY_COOKIES='access_token=\"ABC\"; cf_clearance=xyz'\n"
    )
    monkeypatch.chdir(tmp_path)

    result = _read_env_raw("UDEMY_COOKIES")
    assert result is not None
    assert "access_token" in result
    assert "cf_clearance" in result


def test_read_env_raw_double_quotes(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('UDEMY_COOKIES="token=abc; other=def"\n')
    monkeypatch.chdir(tmp_path)

    result = _read_env_raw("UDEMY_COOKIES")
    assert result == "token=abc; other=def"


def test_read_env_raw_missing_key(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER_KEY=value\n")
    monkeypatch.chdir(tmp_path)

    assert _read_env_raw("UDEMY_COOKIES") is None


def test_read_env_raw_no_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert _read_env_raw("UDEMY_COOKIES") is None


def test_read_env_raw_skips_comments(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("# UDEMY_COOKIES=should_be_ignored\nUDEMY_COOKIES=real_value\n")
    monkeypatch.chdir(tmp_path)

    assert _read_env_raw("UDEMY_COOKIES") == "real_value"