"""Testes do CLI Udemy: parser + integração básica com mocks."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.cli.udemy_cli import build_parser, main


# ─── Parser ────────────────────────────────────────────────────────────────


def test_parser_has_all_expected_flags():
    p = build_parser()
    help_text = p.format_help()
    for flag in ["--cookie", "--url", "--output", "--format", "--lang",
                 "--timestamps", "--merge", "--resume", "--list-langs",
                 "--setup", "--debug"]:
        assert flag in help_text, f"Flag {flag} ausente"


def test_parser_format_choices():
    p = build_parser()
    args = p.parse_args(["--url", "x", "--format", "obsidian"])
    assert args.format == "obsidian"


def test_parser_rejects_invalid_format():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--url", "x", "--format", "notion"])


def test_parser_defaults():
    p = build_parser()
    args = p.parse_args(["--url", "x"])
    assert args.format == "txt"
    assert args.output == "./udemy_transcripts"
    assert args.merge is False
    assert args.resume is False


def test_parser_boolean_flags():
    p = build_parser()
    args = p.parse_args(["--url", "x", "--merge", "--resume", "--timestamps", "--debug"])
    assert args.merge is True
    assert args.resume is True
    assert args.timestamps is True
    assert args.debug is True


# ─── Behavior: fluxo de erro ──────────────────────────────────────────────


def test_main_fails_without_cookie(monkeypatch, capsys):
    """Sem cookie nem no CLI nem no .env → sai com 1 e imprime instruções."""
    monkeypatch.delenv("UDEMY_COOKIES", raising=False)
    monkeypatch.delenv("UDEMY_ACCESS_TOKEN", raising=False)

    # monkeypatch num dir sem .env pra garantir fallback vazio
    monkeypatch.chdir("/tmp")

    rc = main(["--url", "meu-curso"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Cookies não encontrados" in captured.out


def test_main_fails_without_url_when_cookie_present(monkeypatch, tmp_path):
    """Com cookie mas sem --url (e sem --setup) → parser.error sai com 2."""
    monkeypatch.setenv("UDEMY_COOKIES", "access_token=x; cf_clearance=y")
    monkeypatch.chdir(tmp_path)  # dir sem .env

    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


# ─── Behavior: --setup delega pra setup_env ───────────────────────────────


def test_main_setup_delegates(monkeypatch):
    with patch("classroom_transcripter.cli.setup_cli.setup_env") as mock_setup:
        rc = main(["--setup"])
    assert rc == 0
    mock_setup.assert_called_once()


# ─── Behavior: wiring com UdemySource ─────────────────────────────────────


@patch("classroom_transcripter.cli.udemy_cli.UdemySource")
@patch("classroom_transcripter.cli.udemy_cli.download_course")
def test_main_happy_path_wires_source(mock_download, mock_source_cls, monkeypatch, tmp_path):
    """--url chama UdemySource(...).fetch_course() e então download_course()."""
    monkeypatch.setenv("UDEMY_COOKIES", "access_token=x; cf_clearance=y")
    monkeypatch.chdir(tmp_path)

    instance = MagicMock()
    instance.fetch_course.return_value = "course_obj"
    mock_source_cls.return_value = instance

    rc = main(["--url", "meu-curso", "--output", str(tmp_path)])

    assert rc == 0
    mock_source_cls.assert_called_once()
    # cookie e language foram passados
    kwargs = mock_source_cls.call_args.kwargs
    assert "cookie" in kwargs
    assert kwargs["language"] == "pt"

    instance.fetch_course.assert_called_once_with("meu-curso")
    mock_download.assert_called_once()


@patch("classroom_transcripter.cli.udemy_cli.UdemySource")
@patch("classroom_transcripter.cli.udemy_cli.list_available_captions")
@patch("classroom_transcripter.cli.udemy_cli.download_course")
def test_list_langs_doesnt_download(
    mock_download, mock_list, mock_source_cls, monkeypatch, tmp_path,
):
    """--list-langs só lista, não chama download_course."""
    monkeypatch.setenv("UDEMY_COOKIES", "access_token=x; cf_clearance=y")
    monkeypatch.chdir(tmp_path)

    instance = MagicMock()
    instance.fetch_course.return_value = "course_obj"
    mock_source_cls.return_value = instance

    rc = main(["--url", "x", "--list-langs"])

    assert rc == 0
    mock_list.assert_called_once()
    mock_download.assert_not_called()


@patch("classroom_transcripter.cli.udemy_cli.UdemySource")
@patch("classroom_transcripter.cli.udemy_cli.download_course")
def test_obsidian_formatter_gets_platform_udemy(
    mock_download, mock_source_cls, monkeypatch, tmp_path,
):
    """Formato obsidian → ObsidianFormatter recebe platform='udemy'."""
    monkeypatch.setenv("UDEMY_COOKIES", "access_token=x; cf_clearance=y")
    monkeypatch.chdir(tmp_path)

    mock_source_cls.return_value = MagicMock()

    rc = main(["--url", "x", "--format", "obsidian"])

    assert rc == 0
    # Formatter passado pra download_course deve ser ObsidianFormatter com platform=udemy
    from classroom_transcripter.core.formatters import ObsidianFormatter
    formatter = mock_download.call_args.kwargs["formatter"]
    assert isinstance(formatter, ObsidianFormatter)
    assert formatter.platform == "udemy"


@patch("classroom_transcripter.cli.udemy_cli.UdemySource")
@patch("classroom_transcripter.cli.udemy_cli.download_course")
def test_transcripter_error_returns_1(mock_download, mock_source_cls, monkeypatch, tmp_path):
    """Erros do tipo TranscripterError → exit 1, sem stack trace (sem --debug)."""
    from classroom_transcripter.core.exceptions import CourseNotFoundError

    monkeypatch.setenv("UDEMY_COOKIES", "access_token=x; cf_clearance=y")
    monkeypatch.chdir(tmp_path)

    instance = MagicMock()
    instance.fetch_course.side_effect = CourseNotFoundError("slug inválido")
    mock_source_cls.return_value = instance

    rc = main(["--url", "x"])
    assert rc == 1
