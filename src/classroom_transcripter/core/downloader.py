"""Downloader genérico — orquestra transcrição de qualquer `TranscriptSource`.

Antes (v0.1): `downloader.py` conhecia Udemy diretamente.
Agora (v0.2): recebe um `TranscriptSource` abstrato e funciona com Udemy/DIO/Alura.

API pública:
  - download_course(source, course, ...) — orquestração pura (requer Course)
  - download_by_identifier(source, identifier, ...) — conveniência (faz fetch_course)
  - list_available_captions(source, course) — lista idiomas disponíveis

Features preservadas do v0.1:
  ✓ --resume (pula aulas já baixadas)
  ✓ --merge (gera arquivo único com todo o curso)
  ✓ Navegação prev/next pro Obsidian
  ✓ _metadata.json
  ✓ Formatters (txt/obsidian) via BaseFormatter
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from classroom_transcripter.core.config import DOWNLOAD_DELAY
from classroom_transcripter.core.exceptions import (
    TranscriptNotAvailableError,
    TranscripterError,
)
from classroom_transcripter.core.formatters import BaseFormatter, PlainTextFormatter
from classroom_transcripter.core.models import (
    Course,
    DownloadResult,
    Lecture,
    Module,
    Transcript,
)
from classroom_transcripter.core.utils import sanitize_filename
from classroom_transcripter.sources.base import TranscriptSource


# ─── API pública ────────────────────────────────────────────────────────────


def download_course(
    source: TranscriptSource,
    course: Course,
    *,
    output_dir: str | Path = "./transcripts",
    lang: str | None = None,
    with_timestamps: bool = False,
    merge: bool = False,
    formatter: BaseFormatter | None = None,
    resume: bool = False,
) -> DownloadResult:
    """Baixa todas as transcrições de um curso já populado.

    Args:
        source: Fonte implementando TranscriptSource. Usado pra `fetch_transcript`.
        course: Course já com Modules e Lectures populados (normalmente vem de
                `source.fetch_course()` ou `DioSource.fetch_course(path)`).
        output_dir: Diretório raiz de saída. Default: ./transcripts
        lang: Idioma preferido. Se None, source usa seu próprio default.
        with_timestamps: Se True, inclui timestamps no texto formatado.
        merge: Se True, gera arquivo único com todo o curso.
        formatter: PlainTextFormatter por default.
        resume: Se True, pula aulas cujo arquivo já existe em disco.

    Returns:
        DownloadResult com estatísticas.

    Raises:
        TranscriptNotAvailableError: Se NENHUMA aula do curso tem transcrição
            (ex: curso Udemy sem legendas nenhuma).
    """
    if formatter is None:
        formatter = PlainTextFormatter()

    total_lectures = sum(len(m.lectures) for m in course.modules)
    lectures_with_source = _count_lectures_with_transcripts(course.modules)

    print(f"\n🎓 {course.title}")
    print(f"   {len(course.modules)} módulos, {total_lectures} aulas")
    print(f"   {lectures_with_source} aulas com transcrição disponível")

    if lectures_with_source == 0:
        raise TranscriptNotAvailableError(
            f"Curso {course.title!r} não tem nenhuma aula com transcrição disponível."
        )

    if resume:
        print("   ▶ Modo --resume: aulas já baixadas serão puladas")

    course_dir = Path(output_dir) / sanitize_filename(course.title)
    course_dir.mkdir(parents=True, exist_ok=True)

    downloaded, skipped, errors, transcripts = _download_modules(
        source=source,
        course=course,
        course_dir=course_dir,
        with_timestamps=with_timestamps,
        formatter=formatter,
        resume=resume,
    )

    if merge and transcripts:
        merged_content = formatter.format_merged(
            modules=course.modules,
            transcripts=transcripts,
            course_title=course.title,
            total_downloaded=downloaded,
        )
        merged_path = course_dir / formatter.get_merged_filename()
        merged_path.write_text(merged_content, encoding="utf-8")
        print(f"\n📄 Arquivo completo: {merged_path}")

    formatter.save_extras(
        course_dir=course_dir,
        modules=course.modules,
        transcripts=transcripts,
        course_title=course.title,
        slug=course.slug,
    )

    _save_metadata(
        course_dir=course_dir,
        course=course,
        total_lectures=total_lectures,
        downloaded=downloaded,
        skipped=skipped,
        lang=lang,
    )

    print("\n✓ Concluído!")
    print(f"  Transcrições baixadas: {downloaded}")
    if skipped:
        print(f"  Já existiam (puladas): {skipped}")
    if errors:
        print(f"  Erros: {errors}")
    print(f"  Diretório: {course_dir}")

    return DownloadResult(
        course_title=course.title,
        course_id=course.id,
        slug=course.slug,
        platform=course.platform,
        total_modules=len(course.modules),
        total_lectures=total_lectures,
        downloaded=downloaded,
        errors=errors,
        output_dir=str(course_dir),
        skipped=skipped,
    )


def download_by_identifier(
    source: TranscriptSource,
    identifier: str,
    **kwargs,
) -> DownloadResult:
    """Conveniência: faz `fetch_course` + `download_course` numa chamada só.

    Equivalente ao fluxo do v0.1, útil pros CLIs que só recebem uma URL.
    Para DIO, onde `identifier` é um path local, funciona igual.

    Args:
        source: TranscriptSource autenticado.
        identifier: URL, slug, ou path (depende da source).
        **kwargs: repassados pra `download_course`.
    """
    print(f"\n🔍 Buscando curso: {identifier}")
    course = source.fetch_course(identifier)
    return download_course(source, course, **kwargs)


def list_available_captions(
    source: TranscriptSource,
    course: Course,
) -> dict[str, dict]:
    """Lista idiomas de transcrição disponíveis no curso.

    Returns:
        Dict mapeando locale → {"label": str, "count": int}
    """
    print(f"\n🎓 {course.title}")

    langs: dict[str, dict] = {}
    for lecture in course.iter_lectures():
        for cap in lecture.captions:
            if cap.locale not in langs:
                langs[cap.locale] = {"label": cap.label, "count": 0}
            langs[cap.locale]["count"] += 1

    if not langs:
        print("  Nenhuma legenda disponível.")
        return langs

    print("  Idiomas disponíveis:")
    for locale, info in sorted(langs.items(), key=lambda x: -x[1]["count"]):
        print(f"    • {info['label']} ({locale}) — {info['count']} aulas")

    return langs


# ─── Funções internas ──────────────────────────────────────────────────────


def _count_lectures_with_transcripts(modules: list[Module]) -> int:
    """Conta aulas que podem ter transcrição.

    Heurística multi-plataforma:
    - Udemy/Alura: lectures com `captions` populado → têm legenda
    - DIO: lectures com `metadata["file"]` → têm mp4 pra transcrever
    - Se ambos vazios, assume que source lança TranscriptNotAvailableError
      quando chamarmos fetch_transcript
    """
    count = 0
    for module in modules:
        for lecture in module.lectures:
            if lecture.captions or lecture.metadata.get("file"):
                count += 1
    return count


def _lecture_is_available(lecture: Lecture) -> bool:
    """Mesma heurística do contador, pra filtrar lectures no loop."""
    return bool(lecture.captions) or bool(lecture.metadata.get("file"))


def _build_lecture_navigation(
    modules: list[Module],
) -> dict[int | str, tuple[Lecture | None, Lecture | None]]:
    """Constrói mapa de navegação (prev, next) pra cada lecture disponível.

    Usado pelo ObsidianFormatter pra gerar wikilinks [[anterior]] / [[próxima]].
    """
    all_lectures: list[Lecture] = [
        lec
        for module in modules
        for lec in module.lectures
        if _lecture_is_available(lec)
    ]

    nav: dict[int | str, tuple[Lecture | None, Lecture | None]] = {}
    for i, lecture in enumerate(all_lectures):
        prev_lec = all_lectures[i - 1] if i > 0 else None
        next_lec = all_lectures[i + 1] if i < len(all_lectures) - 1 else None
        nav[lecture.id] = (prev_lec, next_lec)

    return nav


def _transcript_to_text(transcript: Transcript, with_timestamps: bool) -> str:
    """Converte um Transcript em string pronta pro formatter.

    Se `with_timestamps=True` e o transcript tem cues, prefixa `[HH:MM:SS]`.
    Senão, usa `plain_text` (fallback: junta cues sem timestamp).
    """
    if with_timestamps and transcript.has_timestamps:
        lines = []
        for cue in transcript.cues:
            ts = _format_seconds(cue.start_seconds)
            lines.append(f"[{ts}] {cue.text}")
        return "\n".join(lines)

    if transcript.plain_text:
        return transcript.plain_text

    # Fallback: monta plain_text a partir de cues se existirem
    if transcript.cues:
        return " ".join(cue.text for cue in transcript.cues)

    return ""


def _format_seconds(total: float) -> str:
    """1234.5 → '00:20:34'"""
    total_int = int(total)
    h, rem = divmod(total_int, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _download_modules(
    source: TranscriptSource,
    course: Course,
    course_dir: Path,
    with_timestamps: bool,
    formatter: BaseFormatter,
    resume: bool = False,
) -> tuple[int, int, int, dict[int | str, str]]:
    """Itera módulos/aulas e baixa as transcrições via `source.fetch_transcript`.

    Returns:
        (downloaded, skipped, errors, transcripts_map)
        transcripts_map: lecture.id → texto formatado (usado pro --merge)
    """
    downloaded = 0
    skipped = 0
    errors = 0
    transcripts: dict[int | str, str] = {}

    nav = _build_lecture_navigation(course.modules)

    for module in course.modules:
        module_dir = course_dir / formatter.get_module_dirname(module)
        module_dir.mkdir(exist_ok=True)

        for lecture in module.lectures:
            if not _lecture_is_available(lecture):
                continue

            filename = formatter.get_lecture_filename(lecture)
            file_path = module_dir / filename
            display_name = filename.removesuffix(formatter.file_extension())

            # --resume: pula se já existe
            if resume and file_path.exists():
                print(f"   ↷ {display_name} (já existe, pulando)")
                try:
                    transcripts[lecture.id] = file_path.read_text(encoding="utf-8")
                except Exception:
                    pass
                skipped += 1
                continue

            print(f"   ⬇ {display_name}")

            try:
                transcript = source.fetch_transcript(lecture)
                raw_text = _transcript_to_text(transcript, with_timestamps)
                transcripts[lecture.id] = raw_text

                prev_lec, next_lec = nav.get(lecture.id, (None, None))
                content = formatter.format_lecture(
                    lecture=lecture,
                    module=module,
                    transcript=raw_text,
                    course_title=course.title,
                    slug=course.slug,
                    prev_lecture=prev_lec,
                    next_lecture=next_lec,
                )

                file_path.write_text(content, encoding="utf-8")
                downloaded += 1
                time.sleep(DOWNLOAD_DELAY)

            except TranscripterError as e:
                # Erros esperados (sem caption, etc) — loga mas não quebra o loop
                print(f"   ✗ {e}")
                errors += 1
            except Exception as e:
                print(f"   ✗ Erro inesperado: {e}")
                errors += 1

    return downloaded, skipped, errors, transcripts


def _save_metadata(
    course_dir: Path,
    course: Course,
    total_lectures: int,
    downloaded: int,
    skipped: int,
    lang: str | None,
) -> None:
    """Salva metadados do curso em `_metadata.json` no output dir."""
    meta = {
        "platform": course.platform,
        "course_id": course.id,
        "title": course.title,
        "slug": course.slug,
        "modules": len(course.modules),
        "total_lectures": total_lectures,
        "transcribed": downloaded,
        "skipped": skipped,
        "language": lang or course.language or "auto",
    }
    meta_path = course_dir / "_metadata.json"
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
