"""Parser de arquivos WebVTT (legendas da Udemy/Alura).

API:
  - parse_vtt(content)           → list[VTTEntry]   (cru, com timestamps textuais)
  - to_plain_text(content)       → str              (texto corrido, sem duplicatas)
  - to_timestamped_text(content) → str              (texto com prefixo [HH:MM:SS])
  - vtt_to_transcript(...)       → Transcript       (NOVO — pipeline v0.2)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from classroom_transcripter.core.models import Transcript, TranscriptCue


@dataclass
class VTTEntry:
    """Entrada individual de uma legenda VTT (representação crua)."""

    start: str  # ex: "00:01:23.456"
    end: str
    text: str


def parse_vtt(content: str) -> list[VTTEntry]:
    """Faz parse de um arquivo VTT e retorna lista de entradas."""
    entries: list[VTTEntry] = []

    for block in re.split(r"\n\n+", content.strip()):
        lines = block.strip().split("\n")
        timestamp_line = None
        text_lines: list[str] = []

        for line in lines:
            if "-->" in line:
                timestamp_line = line
            elif timestamp_line and line.strip():
                text_lines.append(line.strip())

        if timestamp_line and text_lines:
            parts = timestamp_line.split("-->")
            entries.append(
                VTTEntry(
                    start=parts[0].strip(),
                    end=parts[1].strip().split(" ")[0],
                    text=" ".join(text_lines),
                )
            )

    return entries


def _clean_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _deduplicate(entries: list[VTTEntry]) -> list[tuple[VTTEntry, str]]:
    """Retorna entradas com texto limpo, sem duplicatas consecutivas."""
    seen: set[str] = set()
    results: list[tuple[VTTEntry, str]] = []
    for entry in entries:
        clean = _clean_html_tags(entry.text)
        if clean and clean not in seen:
            seen.add(clean)
            results.append((entry, clean))
    return results


def to_plain_text(vtt_content: str) -> str:
    """VTT → texto corrido, sem duplicatas."""
    pairs = _deduplicate(parse_vtt(vtt_content))
    return " ".join(text for _, text in pairs)


def to_timestamped_text(vtt_content: str) -> str:
    """VTT → texto com timestamps `[HH:MM:SS] trecho`."""
    pairs = _deduplicate(parse_vtt(vtt_content))
    lines = []
    for entry, text in pairs:
        ts = entry.start.split(".")[0]  # Remove milissegundos
        lines.append(f"[{ts}] {text}")
    return "\n".join(lines)


# ─── v0.2: integração com o modelo Transcript ──────────────────────────────


_TS_PATTERN = re.compile(r"(?:(\d+):)?(\d+):(\d+)(?:\.(\d+))?")


def _timestamp_to_seconds(ts: str) -> float:
    """Converte '01:23:45.678' ou '23:45' em segundos."""
    m = _TS_PATTERN.match(ts)
    if not m:
        return 0.0
    h, mnt, s, ms = m.groups()
    total = int(mnt) * 60 + int(s)
    if h:
        total += int(h) * 3600
    if ms:
        total += int(ms) / (10 ** len(ms))
    return float(total)


def vtt_to_transcript(
    vtt_content: str,
    *,
    lecture_id: int | str,
    language: str,
) -> Transcript:
    """Parseia VTT e devolve um `Transcript` populado com cues E plain_text.

    Uso típico: a `UdemySource.fetch_transcript()` chama essa função
    pra converter o VTT remoto no tipo uniforme do core.
    """
    entries = _deduplicate(parse_vtt(vtt_content))
    cues = [
        TranscriptCue(
            start_seconds=_timestamp_to_seconds(entry.start),
            end_seconds=_timestamp_to_seconds(entry.end),
            text=text,
        )
        for entry, text in entries
    ]
    plain = " ".join(text for _, text in entries)
    return Transcript(
        lecture_id=lecture_id,
        language=language,
        cues=cues,
        plain_text=plain,
    )
