"""Testes do dispatcher `classroom <subcomando>`."""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from classroom_transcripter.cli.main import main


def test_no_args_prints_usage(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom"])
    rc = main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "udemy" in out
    assert "dio" in out
    assert "alura" in out
    assert "enrich" in out
    assert "setup" in out


def test_help_flag_prints_usage(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "--help"])
    assert main() == 0
    assert "udemy" in capsys.readouterr().out


def test_unknown_subcommand_returns_2(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "coursera"])
    assert main() == 2


@patch("classroom_transcripter.cli.udemy_cli.main", return_value=0)
def test_dispatches_to_udemy(udemy_main, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "udemy", "--url", "x"])
    # O dispatcher removerá "udemy" e repassará restante
    assert main() == 0
    udemy_main.assert_called_once()


@patch("classroom_transcripter.cli.enrich_cli.main", return_value=0)
def test_dispatches_to_enrich(enrich_main, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["classroom", "enrich", str(tmp_path)])
    assert main() == 0
    enrich_main.assert_called_once()


@patch("classroom_transcripter.cli.setup_cli.main", return_value=0)
def test_dispatches_to_setup(setup_main, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "setup"])
    assert main() == 0
    setup_main.assert_called_once()


@patch("classroom_transcripter.cli.dio_cli.main", return_value=0)
def test_dispatches_to_dio(dio_main, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "dio", "--video-dir", "/tmp"])
    assert main() == 0
    dio_main.assert_called_once()


@patch("classroom_transcripter.cli.alura_cli.main", return_value=0)
def test_dispatches_to_alura(alura_main, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["classroom", "alura", "--url", "x"])
    assert main() == 0
    alura_main.assert_called_once()
