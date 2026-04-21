"""Testes do core.config."""
import os
from pathlib import Path

from classroom_transcripter.core import config as cfg


def test_default_lang_priority_when_not_set(monkeypatch):
    monkeypatch.delenv("LANG_PRIORITY", raising=False)
    assert "pt" in cfg.get_lang_priority()
    assert "en" in cfg.get_lang_priority()


def test_custom_lang_priority_from_env(monkeypatch):
    monkeypatch.setenv("LANG_PRIORITY", "fr,it,de")
    assert cfg.get_lang_priority() == ["fr", "it", "de"]


def test_udemy_constants_exist():
    assert cfg.UDEMY_BASE_URL == "https://www.udemy.com"
    assert cfg.UDEMY_API_BASE.endswith("/api-2.0")
    assert cfg.CURRICULUM_PAGE_SIZE > 0


def test_backwards_compat_aliases():
    """Aliases v0.1 (BASE_URL, API_BASE, HEADERS_BASE) mantidos."""
    assert cfg.BASE_URL == cfg.UDEMY_BASE_URL
    assert cfg.API_BASE == cfg.UDEMY_API_BASE
    assert cfg.HEADERS_BASE == cfg.UDEMY_HEADERS_BASE


def test_whisper_defaults(monkeypatch):
    monkeypatch.delenv("WHISPER_MODEL", raising=False)
    monkeypatch.delenv("WHISPER_LANGUAGE", raising=False)
    assert cfg.get_whisper_model() == "small"
    assert cfg.get_whisper_language() == "pt"


def test_whisper_from_env(monkeypatch):
    monkeypatch.setenv("WHISPER_MODEL", "medium")
    monkeypatch.setenv("WHISPER_LANGUAGE", "en")
    assert cfg.get_whisper_model() == "medium"
    assert cfg.get_whisper_language() == "en"


def test_dio_video_dir_default(monkeypatch):
    monkeypatch.delenv("DIO_VIDEO_DIR", raising=False)
    assert cfg.get_dio_video_dir() == Path("./dio_videos")


def test_dio_video_dir_from_env(monkeypatch):
    monkeypatch.setenv("DIO_VIDEO_DIR", "/tmp/videos")
    assert cfg.get_dio_video_dir() == Path("/tmp/videos")


def test_alura_credentials_empty_by_default(monkeypatch):
    monkeypatch.delenv("ALURA_EMAIL", raising=False)
    monkeypatch.delenv("ALURA_PASSWORD", raising=False)
    email, pw = cfg.get_alura_credentials()
    assert email == ""
    assert pw == ""


def test_alura_credentials_from_env(monkeypatch):
    monkeypatch.setenv("ALURA_EMAIL", "a@b.com")
    monkeypatch.setenv("ALURA_PASSWORD", "secret")
    assert cfg.get_alura_credentials() == ("a@b.com", "secret")


def test_resolve_cookies_cli_has_priority(monkeypatch):
    monkeypatch.setenv("UDEMY_COOKIES", "from_env")
    assert cfg.resolve_cookies("from_cli") == "from_cli"


def test_resolve_cookies_falls_back_to_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # _read_env_raw procura .env no cwd
    monkeypatch.setenv("UDEMY_COOKIES", "env_value_with_enough_length_to_pass_check_; extra=1")
    assert cfg.resolve_cookies(None).startswith("env_value")
