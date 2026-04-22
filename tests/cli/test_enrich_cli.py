"""Testes do CLI enrich."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.cli.enrich_cli import build_parser, main


# ─── Parser ────────────────────────────────────────────────────────────────


def test_parser_has_expected_flags():
    p = build_parser()
    help_text = p.format_help()
    for flag in ["--provider", "--model", "--api-key", "--ollama-url",
                 "--delay", "--timeout", "--dry-run", "--debug"]:
        assert flag in help_text


def test_parser_directory_is_positional():
    p = build_parser()
    args = p.parse_args(["./transcripts"])
    assert args.directory == "./transcripts"
    assert args.provider == "ollama"  # default


def test_parser_provider_choices():
    p = build_parser()
    for provider in ["ollama", "claude", "groq", "gemini"]:
        args = p.parse_args(["./x", "--provider", provider])
        assert args.provider == provider


def test_parser_rejects_unknown_provider():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["./x", "--provider", "openai"])


def test_parser_defaults():
    p = build_parser()
    args = p.parse_args(["./x"])
    assert args.delay == 1.0
    assert args.timeout == 900
    assert args.dry_run is False


# ─── Behavior ──────────────────────────────────────────────────────────────


def test_main_fails_on_missing_directory(capsys, tmp_path):
    rc = main([str(tmp_path / "nao-existe")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "não encontrado" in captured.out.lower()


@patch("classroom_transcripter.cli.enrich_cli.create_provider")
@patch("classroom_transcripter.cli.enrich_cli.enrich_directory")
def test_main_happy_path(mock_enrich, mock_factory, tmp_path):
    mock_factory.return_value = MagicMock()

    rc = main([str(tmp_path), "--provider", "groq"])

    assert rc == 0
    mock_factory.assert_called_once()
    factory_kwargs = mock_factory.call_args.kwargs
    assert factory_kwargs["provider_name"] == "groq"
    mock_enrich.assert_called_once()


@patch("classroom_transcripter.cli.enrich_cli.create_provider")
def test_main_reports_factory_error(mock_factory, tmp_path, capsys):
    """ValueError do factory (ex: API key ausente) → exit 1."""
    from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError

    mock_factory.side_effect = ProviderAPIKeyMissingError("GROQ_API_KEY não encontrada")

    rc = main([str(tmp_path), "--provider", "groq"])
    # ProviderAPIKeyMissingError é ValueError-like mas herda de TranscripterError
    # O CLI só pega ValueError na factory, então vai cair no except genérico
    assert rc == 1


@patch("classroom_transcripter.cli.enrich_cli.create_provider")
@patch("classroom_transcripter.cli.enrich_cli.enrich_directory")
def test_main_forwards_cli_args_to_factory(mock_enrich, mock_factory, tmp_path):
    mock_factory.return_value = MagicMock()
    main([
        str(tmp_path),
        "--provider", "ollama",
        "--model", "qwen2.5:14b",
        "--ollama-url", "http://homelab:11434",
        "--timeout", "1200",
    ])

    kwargs = mock_factory.call_args.kwargs
    assert kwargs["model"] == "qwen2.5:14b"
    assert kwargs["base_url"] == "http://homelab:11434"
    assert kwargs["timeout"] == 1200


@patch("classroom_transcripter.cli.enrich_cli.create_provider")
@patch("classroom_transcripter.cli.enrich_cli.enrich_directory")
def test_main_forwards_dry_run_and_delay(mock_enrich, mock_factory, tmp_path):
    mock_factory.return_value = MagicMock()
    main([str(tmp_path), "--dry-run", "--delay", "0.5"])

    kwargs = mock_enrich.call_args.kwargs
    assert kwargs["dry_run"] is True
    assert kwargs["delay"] == 0.5
