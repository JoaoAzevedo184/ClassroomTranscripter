"""Lógica principal de download e salvamento de transcrições."""

import json
import time
from pathlib import Path

import requests

from .client import UdemyClient
from .config import DOWNLOAD_DELAY
from .exceptions import NoCaptionsError
from .models import DownloadResult, Section
from .utils import pick_caption, sanitize_filename
from .vtt import to_plain_text, to_timestamped_text


def list_available_captions(client: UdemyClient, slug: str) -> dict[str, dict]:
    """Lista os idiomas de legenda disponíveis no curso.

    Returns:
        Dict mapeando locale -> {"label": str, "count": int}
    """
    course_id, title = client.get_course_info(slug)
    print(f"\n🎓 {title}")

    sections = client.get_curriculum(course_id)
    langs: dict[str, dict] = {}

    for section in sections:
        for lecture in section.lectures:
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


def download_transcripts(
    client: UdemyClient,
    slug: str,
    output_dir: str = "./udemy_transcripts",
    lang: str | None = None,
    with_timestamps: bool = False,
    merge: bool = False,
) -> DownloadResult:
    """Baixa todas as transcrições de um curso.

    Args:
        client: Cliente autenticado da Udemy.
        slug: Slug do curso.
        output_dir: Diretório raiz de saída.
        lang: Idioma preferido (ex: "pt", "en").
        with_timestamps: Se True, inclui timestamps [HH:MM:SS].
        merge: Se True, gera arquivo único _CURSO_COMPLETO.txt.

    Returns:
        DownloadResult com estatísticas do download.

    Raises:
        NoCaptionsError: Se nenhuma legenda estiver disponível.
    """
    # Busca informações do curso
    print(f"\n🎓 Buscando informações do curso: {slug}")
    course_id, course_title = client.get_course_info(slug)
    print(f"   Título: {course_title}")
    print(f"   ID: {course_id}")

    # Busca grade curricular
    print("\n📚 Carregando grade curricular...")
    sections = client.get_curriculum(course_id)
    total_lectures = sum(len(s.lectures) for s in sections)
    lectures_with_caps = sum(
        1 for s in sections for lec in s.lectures if lec.captions
    )
    print(f"   {len(sections)} seções, {total_lectures} aulas")
    print(f"   {lectures_with_caps} aulas com transcrição disponível")

    if lectures_with_caps == 0:
        raise NoCaptionsError()

    # Prepara diretórios
    course_dir = Path(output_dir) / sanitize_filename(course_title)
    course_dir.mkdir(parents=True, exist_ok=True)

    # Faz o download
    downloaded, errors, merged_content = _download_sections(
        sections=sections,
        course_dir=course_dir,
        lang=lang,
        with_timestamps=with_timestamps,
        collect_merge=merge,
    )

    # Salva arquivo mesclado
    if merge and merged_content:
        _save_merged_file(course_dir, course_title, downloaded, merged_content)

    # Salva metadados
    _save_metadata(
        course_dir, course_id, course_title, slug,
        len(sections), total_lectures, downloaded, lang,
    )

    # Relatório final
    print("\n✓ Concluído!")
    print(f"  Transcrições salvas: {downloaded}")
    if errors:
        print(f"  Erros: {errors}")
    print(f"  Diretório: {course_dir}")

    return DownloadResult(
        course_title=course_title,
        course_id=course_id,
        slug=slug,
        total_sections=len(sections),
        total_lectures=total_lectures,
        downloaded=downloaded,
        errors=errors,
        output_dir=str(course_dir),
    )


# ─── Funções internas ──────────────────────────────────────────────────────


def _download_sections(
    sections: list[Section],
    course_dir: Path,
    lang: str | None,
    with_timestamps: bool,
    collect_merge: bool,
) -> tuple[int, int, list[str]]:
    """Itera sobre seções/aulas e baixa as legendas.

    Returns:
        Tupla (downloaded, errors, merged_content).
    """
    downloaded = 0
    errors = 0
    merged_content: list[str] = []

    for section in sections:
        section_name = f"{section.index:02d} - {sanitize_filename(section.title)}"
        section_dir = course_dir / section_name
        section_dir.mkdir(exist_ok=True)

        if collect_merge:
            merged_content.append(f"\n{'='*60}")
            merged_content.append(f"SEÇÃO: {section.title}")
            merged_content.append(f"{'='*60}\n")

        for lecture in section.lectures:
            caption = pick_caption(lecture.captions, lang)
            if not caption:
                continue

            lecture_name = (
                f"{lecture.object_index:03d} - {sanitize_filename(lecture.title)}"
            )
            print(f"   ⬇ {lecture_name} [{caption.label}]")

            try:
                text = _fetch_and_convert(
                    caption.url, with_timestamps
                )
                # Salva arquivo individual
                txt_path = section_dir / f"{lecture_name}.txt"
                txt_path.write_text(text, encoding="utf-8")

                if collect_merge:
                    merged_content.append(f"\n--- {lecture.title} ---\n")
                    merged_content.append(text)
                    merged_content.append("")

                downloaded += 1
                time.sleep(DOWNLOAD_DELAY)

            except Exception as e:
                print(f"   ✗ Erro: {e}")
                errors += 1

    return downloaded, errors, merged_content


def _fetch_and_convert(url: str, with_timestamps: bool) -> str:
    """Baixa um arquivo VTT e converte para texto."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    vtt_content = resp.text

    if with_timestamps:
        return to_timestamped_text(vtt_content)
    return to_plain_text(vtt_content)


def _save_merged_file(
    course_dir: Path,
    course_title: str,
    downloaded: int,
    merged_content: list[str],
) -> None:
    """Salva o arquivo mesclado _CURSO_COMPLETO.txt."""
    merged_path = course_dir / "_CURSO_COMPLETO.txt"
    header = (
        f"Curso: {course_title}\n"
        f"Total de aulas transcritas: {downloaded}\n"
        f"{'='*60}\n"
    )
    merged_path.write_text(
        header + "\n".join(merged_content), encoding="utf-8"
    )
    print(f"\n📄 Arquivo completo: {merged_path}")


def _save_metadata(
    course_dir: Path,
    course_id: int,
    course_title: str,
    slug: str,
    total_sections: int,
    total_lectures: int,
    downloaded: int,
    lang: str | None,
) -> None:
    """Salva metadados do curso em JSON."""
    meta = {
        "course_id": course_id,
        "title": course_title,
        "slug": slug,
        "sections": total_sections,
        "total_lectures": total_lectures,
        "transcribed": downloaded,
        "language": lang or "auto",
    }
    meta_path = course_dir / "_metadata.json"
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )