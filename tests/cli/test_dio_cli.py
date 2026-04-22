"""Testes do CLI DIO."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from classroom_transcripter.cli.dio_cli import build_parser, main


def test_parser_requires_video_dir():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args([])


def test_parser_accepts_video_dir():
    p = build_parser()
    args = p.parse_args(["--video-dir", "/tmp/x"])
    assert args.video_dir == "/tmp/x"


def test_parser_whisper_model_choices():
    p = build_parser()
    for m in ["tiny", "base", "small", "medium", "large"]:
        args = p.parse_args(["--video-dir", "x", "--whisper-model", m])
        assert args.whisper_model == m


def test_parser_rejects_invalid_whisper_model():
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--video-dir", "x", "--whisper-model", "enormous"])


def test_parser_default_format_is_obsidian():
    """DIO faz sentido default pra obsidian — timestamps são naturais."""
    p = build_parser()
    args = p.parse_args(["--video-dir", "x"])
    assert args.format == "obsidian"


def test_parser_resume_flag():
    p = build_parser()
    args = p.parse_args(["--video-dir", "x", "--resume"])
    assert args.resume is True


# ─── Wiring ───────────────────────────────────────────────────────────────


@patch("classroom_transcripter.cli.dio_cli.DioSource")
@patch("classroom_transcripter.cli.dio_cli.download_course")
def test_main_wires_source_with_correct_args(mock_download, mock_source_cls, tmp_path):
    instance = MagicMock()
    instance.fetch_course.return_value = "course_obj"
    mock_source_cls.return_value = instance

    rc = main([
        "--video-dir", str(tmp_path),
        "--whisper-model", "medium",
        "--lang", "en",
    ])

    assert rc == 0
    kwargs = mock_source_cls.call_args.kwargs
    assert kwargs["whisper_model"] == "medium"
    assert kwargs["language"] == "en"


@patch("classroom_transcripter.cli.dio_cli.DioSource")
@patch("classroom_transcripter.cli.dio_cli.download_course")
def test_main_uses_env_defaults(mock_download, mock_source_cls, monkeypatch, tmp_path):
    monkeypatch.setenv("WHISPER_MODEL", "tiny")
    monkeypatch.setenv("WHISPER_LANGUAGE", "es")
    mock_source_cls.return_value = MagicMock()

    main(["--video-dir", str(tmp_path)])
    kwargs = mock_source_cls.call_args.kwargs
    assert kwargs["whisper_model"] == "tiny"
    assert kwargs["language"] == "es"


@patch("classroom_transcripter.cli.dio_cli.DioSource")
@patch("classroom_transcripter.cli.dio_cli.download_course")
def test_main_passes_platform_dio_to_obsidian(mock_download, mock_source_cls, tmp_path):
    mock_source_cls.return_value = MagicMock()
    main(["--video-dir", str(tmp_path), "--format", "obsidian"])

    from classroom_transcripter.core.formatters import ObsidianFormatter
    formatter = mock_download.call_args.kwargs["formatter"]
    assert isinstance(formatter, ObsidianFormatter)
    assert formatter.platform == "dio"


@patch("classroom_transcripter.cli.dio_cli.DioSource")
@patch("classroom_transcripter.cli.dio_cli.download_course")
def test_main_forwards_resume_flag(mock_download, mock_source_cls, tmp_path):
    mock_source_cls.return_value = MagicMock()
    main(["--video-dir", str(tmp_path), "--resume"])
    assert mock_download.call_args.kwargs["resume"] is True


@patch("classroom_transcripter.cli.dio_cli.DioSource")
@patch("classroom_transcripter.cli.dio_cli.download_course")
def test_main_transcripter_error_returns_1(mock_download, mock_source_cls, tmp_path):
    from classroom_transcripter.core.exceptions import CourseNotFoundError

    instance = MagicMock()
    instance.fetch_course.side_effect = CourseNotFoundError("não encontrada")
    mock_source_cls.return_value = instance

    rc = main(["--video-dir", str(tmp_path)])
    assert rc == 1
