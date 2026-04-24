"""Testes do CLI Alura."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.cli.alura_cli import build_parser, main


def test_parser_requires_url():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args([])


def test_parser_accepts_url():
    p = build_parser()
    args = p.parse_args(["--url", "x"])
    assert args.url == "x"


def test_parser_default_format_is_obsidian():
    p = build_parser()
    args = p.parse_args(["--url", "x"])
    assert args.format == "obsidian"


def test_parser_flags():
    p = build_parser()
    args = p.parse_args(["--url", "x", "--merge", "--resume", "--ask-password"])
    assert args.merge is True
    assert args.resume is True
    assert args.ask_password is True


# ─── Credenciais ──────────────────────────────────────────────────────────


def test_main_fails_without_email(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ALURA_EMAIL", raising=False)
    monkeypatch.delenv("ALURA_PASSWORD", raising=False)
    monkeypatch.chdir(tmp_path)

    rc = main(["--url", "x", "--password", "p"])
    assert rc == 1
    assert "Email não encontrado" in capsys.readouterr().out


def test_main_fails_without_password(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ALURA_EMAIL", raising=False)
    monkeypatch.delenv("ALURA_PASSWORD", raising=False)
    monkeypatch.chdir(tmp_path)

    rc = main(["--url", "x", "--email", "e@x.com"])
    assert rc == 1
    assert "Senha não encontrada" in capsys.readouterr().out


def test_main_reads_credentials_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ALURA_EMAIL", "env@x.com")
    monkeypatch.setenv("ALURA_PASSWORD", "envpass")
    monkeypatch.chdir(tmp_path)

    with patch("classroom_transcripter.cli.alura_cli.AluraSource") as mock_src:
        mock_src.return_value = MagicMock()
        with patch("classroom_transcripter.cli.alura_cli.download_course"):
            main(["--url", "x"])

    kwargs = mock_src.call_args.kwargs
    assert kwargs["email"] == "env@x.com"
    assert kwargs["password"] == "envpass"


def test_cli_email_overrides_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ALURA_EMAIL", "env@x.com")
    monkeypatch.setenv("ALURA_PASSWORD", "envpass")
    monkeypatch.chdir(tmp_path)

    with patch("classroom_transcripter.cli.alura_cli.AluraSource") as mock_src:
        mock_src.return_value = MagicMock()
        with patch("classroom_transcripter.cli.alura_cli.download_course"):
            main(["--url", "x", "--email", "cli@x.com"])

    assert mock_src.call_args.kwargs["email"] == "cli@x.com"


# ─── NotImplementedError dos TODOs ────────────────────────────────────────


def test_not_implemented_shows_friendly_message(capsys, monkeypatch, tmp_path):
    """Sem preencher os TODOs, o CLI deve explicar como ativar a Fase 7."""
    monkeypatch.setenv("ALURA_EMAIL", "e@x.com")
    monkeypatch.setenv("ALURA_PASSWORD", "p")
    monkeypatch.chdir(tmp_path)

    with patch("classroom_transcripter.cli.alura_cli.AluraSource") as mock_src:
        instance = MagicMock()
        instance.fetch_course.side_effect = NotImplementedError(
            "TODO Fase 7.1: preencher AluraClient.login()"
        )
        mock_src.return_value = instance

        rc = main(["--url", "x"])

    assert rc == 1
    output = capsys.readouterr().out
    assert "Fase 7" in output
    assert "docs/sources/alura.md" in output


# ─── Wiring ───────────────────────────────────────────────────────────────


def test_main_passes_platform_alura_to_obsidian(monkeypatch, tmp_path):
    monkeypatch.setenv("ALURA_EMAIL", "e@x.com")
    monkeypatch.setenv("ALURA_PASSWORD", "p")
    monkeypatch.chdir(tmp_path)

    with patch("classroom_transcripter.cli.alura_cli.AluraSource") as mock_src:
        mock_src.return_value = MagicMock()
        with patch("classroom_transcripter.cli.alura_cli.download_course") as mock_dl:
            main(["--url", "x", "--format", "obsidian"])

    from classroom_transcripter.core.formatters import ObsidianFormatter
    formatter = mock_dl.call_args.kwargs["formatter"]
    assert isinstance(formatter, ObsidianFormatter)
    assert formatter.platform == "alura"


def test_main_forwards_resume_and_merge(monkeypatch, tmp_path):
    monkeypatch.setenv("ALURA_EMAIL", "e@x.com")
    monkeypatch.setenv("ALURA_PASSWORD", "p")
    monkeypatch.chdir(tmp_path)

    with patch("classroom_transcripter.cli.alura_cli.AluraSource") as mock_src:
        mock_src.return_value = MagicMock()
        with patch("classroom_transcripter.cli.alura_cli.download_course") as mock_dl:
            main(["--url", "x", "--resume", "--merge"])

    kwargs = mock_dl.call_args.kwargs
    assert kwargs["resume"] is True
    assert kwargs["merge"] is True
