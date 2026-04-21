"""Testes do parser VTT."""
from classroom_transcripter.core.vtt import (
    VTTEntry,
    parse_vtt,
    to_plain_text,
    to_timestamped_text,
    vtt_to_transcript,
)


VTT_SAMPLE = """\
WEBVTT

00:00:01.000 --> 00:00:03.000
Olá pessoal

00:00:03.500 --> 00:00:06.000
Bem-vindos ao curso

00:00:06.500 --> 00:00:08.000
Bem-vindos ao curso
"""


def test_parse_vtt_returns_entries():
    entries = parse_vtt(VTT_SAMPLE)
    assert len(entries) == 3
    assert all(isinstance(e, VTTEntry) for e in entries)
    assert entries[0].start == "00:00:01.000"


def test_parse_vtt_captures_text():
    entries = parse_vtt(VTT_SAMPLE)
    assert entries[0].text == "Olá pessoal"


def test_to_plain_text_deduplicates():
    result = to_plain_text(VTT_SAMPLE)
    # "Bem-vindos ao curso" aparece 2x, deve aparecer 1x no resultado
    assert result.count("Bem-vindos ao curso") == 1


def test_to_plain_text_joins_with_space():
    result = to_plain_text(VTT_SAMPLE)
    assert "Olá pessoal Bem-vindos ao curso" == result


def test_to_timestamped_text_format():
    result = to_timestamped_text(VTT_SAMPLE)
    assert "[00:00:01]" in result
    assert "[00:00:03]" in result


def test_to_timestamped_text_strips_ms():
    """Milissegundos não devem aparecer no timestamp textual."""
    result = to_timestamped_text(VTT_SAMPLE)
    assert ".000" not in result


def test_vtt_to_transcript_returns_transcript():
    t = vtt_to_transcript(VTT_SAMPLE, lecture_id=42, language="pt")
    assert t.lecture_id == 42
    assert t.language == "pt"
    assert t.has_timestamps
    assert len(t.cues) == 2  # depois de dedup


def test_vtt_to_transcript_cue_seconds():
    t = vtt_to_transcript(VTT_SAMPLE, lecture_id=1, language="pt")
    assert t.cues[0].start_seconds == 1.0
    assert t.cues[0].end_seconds == 3.0
    assert t.cues[1].start_seconds == 3.5


def test_vtt_to_transcript_populates_plain_text():
    t = vtt_to_transcript(VTT_SAMPLE, lecture_id=1, language="pt")
    assert "Olá pessoal" in t.plain_text
    assert "Bem-vindos ao curso" in t.plain_text


def test_parse_vtt_strips_html_tags():
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<i>itálico</i>\n"
    result = to_plain_text(vtt)
    assert result == "itálico"
