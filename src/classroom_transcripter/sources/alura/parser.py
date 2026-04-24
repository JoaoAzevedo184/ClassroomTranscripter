"""Parsing de respostas da Alura pra modelos do core.

Implementado COMPLETO (não é TODO): assume um formato razoável de dict bruto
vindo do client. Se a API real devolver formato diferente, ajuste as funções
aqui — mas a estrutura (course → modules → lectures → transcript) continua.
"""
from __future__ import annotations

from classroom_transcripter.core.models import (
    Course,
    Lecture,
    Module,
    Transcript,
    TranscriptCue,
)
from classroom_transcripter.core.vtt import vtt_to_transcript


# ─── Course / Modules / Lectures ───────────────────────────────────────────


def parse_course(raw: dict, slug: str) -> Course:
    """Converte o dict bruto de `AluraClient.get_course()` num `Course`.

    Estrutura esperada do `raw` (ver client.py para descrição completa):
        {
            "id": str | int,
            "title": str,
            "sections": [
                {
                    "id": str,
                    "title": str,
                    "index": int,
                    "activities": [
                        {"id": str, "title": str, "index": int, "type": str},
                        ...
                    ]
                }
            ]
        }
    """
    modules = [_parse_module(section) for section in raw.get("sections", [])]

    return Course(
        id=raw.get("id", slug),
        slug=slug,
        title=raw.get("title", slug),
        platform="alura",
        modules=modules,
        language=raw.get("language"),
        instructor=raw.get("instructor"),
        metadata={"raw_type": "alura_curriculum"},
    )


def _parse_module(section: dict) -> Module:
    lectures = [
        _parse_lecture(activity, module_index=section.get("index", 0))
        for activity in section.get("activities", [])
    ]
    return Module(
        title=section.get("title", "Sem título"),
        index=section.get("index", 0),
        lectures=lectures,
    )


def _parse_lecture(activity: dict, module_index: int) -> Lecture:
    return Lecture(
        id=activity["id"],
        title=activity.get("title", "Sem título"),
        object_index=activity.get("index", 0),
        # Metadata guarda contexto pro fetch_transcript saber como achar depois
        metadata={
            "type": activity.get("type", "video"),
            "module_index": module_index,
        },
    )


# ─── Transcript ────────────────────────────────────────────────────────────


def parse_transcript(
    raw: dict,
    *,
    lecture_id: int | str,
    default_language: str = "pt",
) -> Transcript:
    """Converte o dict bruto de `get_transcript()` num `Transcript`.

    Suporta 3 formatos:
      A) {"segments": [{"start": float, "end": float, "text": str}, ...], "language": ...}
      B) {"transcript": "texto corrido", "language": ...}
         ou {"text": "texto corrido"}
      C) {"format": "vtt", "content": "WEBVTT\\n..."}
    """
    # FORMATO C — VTT cru delegado ao parser do core
    if raw.get("format") == "vtt" and "content" in raw:
        return vtt_to_transcript(
            raw["content"],
            lecture_id=lecture_id,
            language=raw.get("language", default_language),
        )

    language = raw.get("language", default_language)

    # FORMATO A — Segments estruturados
    if "segments" in raw and isinstance(raw["segments"], list):
        cues = [
            TranscriptCue(
                start_seconds=float(seg["start"]),
                end_seconds=float(seg["end"]),
                text=str(seg["text"]).strip(),
            )
            for seg in raw["segments"]
        ]
        plain = " ".join(c.text for c in cues)
        return Transcript(
            lecture_id=lecture_id,
            language=language,
            cues=cues,
            plain_text=plain,
        )

    # FORMATO B — Texto corrido
    text = raw.get("transcript") or raw.get("text") or ""
    return Transcript(
        lecture_id=lecture_id,
        language=language,
        plain_text=text.strip(),
    )
