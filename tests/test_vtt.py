"""Testes do parser VTT."""

from udemy_transcripter.vtt import parse_vtt, to_plain_text, to_timestamped_text

SAMPLE_VTT = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
Olá, bem-vindos ao curso.

2
00:00:03.500 --> 00:00:06.000
Hoje vamos aprender <b>Docker</b>.

3
00:00:06.500 --> 00:00:09.000
Olá, bem-vindos ao curso.
"""


def test_parse_vtt_extracts_entries():
    entries = parse_vtt(SAMPLE_VTT)
    assert len(entries) == 3
    assert entries[0].start == "00:00:01.000"
    assert entries[0].end == "00:00:03.000"
    assert entries[0].text == "Olá, bem-vindos ao curso."


def test_to_plain_text_deduplicates():
    text = to_plain_text(SAMPLE_VTT)
    assert text.count("Olá, bem-vindos ao curso.") == 1
    assert "Docker" in text
    assert "<b>" not in text


def test_to_timestamped_text():
    text = to_timestamped_text(SAMPLE_VTT)
    assert "[00:00:01]" in text
    assert "[00:00:03]" in text
    assert text.count("Olá, bem-vindos ao curso.") == 1


def test_parse_vtt_empty():
    assert parse_vtt("") == []
    assert parse_vtt("WEBVTT\n\n") == []