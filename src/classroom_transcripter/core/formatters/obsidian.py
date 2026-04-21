"""Formatter Markdown para Obsidian.

Gera notas com:
- Frontmatter YAML (tags, metadados do curso, **platform** na v0.2)
- Wikilinks de navegação entre aulas ([[prev]] / [[next]])
- MOC (Map of Content) com links para todas as notas
- Índice por módulo
- Callouts do Obsidian para navegação
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from classroom_transcripter.core.formatters.base import BaseFormatter
from classroom_transcripter.core.models import Lecture, Module
from classroom_transcripter.core.utils import sanitize_filename


class ObsidianFormatter(BaseFormatter):
    """Markdown otimizado pro Obsidian."""

    def __init__(self, platform: str = "udemy"):
        """
        Args:
            platform: nome da plataforma pra adicionar como tag e frontmatter.
                      v0.2: default "udemy" mantém compatibilidade; Source pode passar
                      "dio" ou "alura" pra marcar notas por origem.
        """
        self.platform = platform

    def file_extension(self) -> str:
        return ".md"

    def format_lecture(
        self,
        lecture: Lecture,
        module: Module,
        transcript: str,
        course_title: str,
        slug: str,
        prev_lecture: Lecture | None = None,
        next_lecture: Lecture | None = None,
    ) -> str:
        course_tag = _slugify_tag(course_title)
        module_tag = _slugify_tag(module.title)

        lines = [
            "---",
            f'course: "{course_title}"',
            f'section: "{module.title}"',
            f"lecture: {lecture.object_index}",
            f"{self.platform}_id: {lecture.id}",
            f"platform: {self.platform}",  # NOVO v0.2
            f"date: {date.today().isoformat()}",
            "tags:",
            f"  - {self.platform}",  # tag dinâmica (antes era hard-coded "udemy")
            f"  - curso/{course_tag}",
            f"  - secao/{module_tag}",
            "---",
            "",
            f"# {lecture.title}",
            "",
        ]

        nav = _build_nav_callout(lecture, prev_lecture, next_lecture)
        if nav:
            lines.append(nav)
            lines.append("")

        lines.append("## Transcrição")
        lines.append("")

        paragraphs = _split_into_paragraphs(transcript)
        for paragraph in paragraphs:
            lines.append(paragraph)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Anotações")
        lines.append("")
        lines.append("> [!note] Espaço para suas anotações")
        lines.append("> ")
        lines.append("")

        return "\n".join(lines)

    def format_merged(
        self,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        total_downloaded: int,
    ) -> str:
        lines = [
            "---",
            f'course: "{course_title}"',
            f"platform: {self.platform}",  # NOVO v0.2
            "tags:",
            f"  - {self.platform}",
            f"  - curso/{_slugify_tag(course_title)}",
            "  - resumo",
            "---",
            "",
            f"# {course_title} — Transcrição Completa",
            "",
            f"> [!info] {total_downloaded} aulas transcritas",
            "",
        ]

        for module in modules:
            module_lectures = [lec for lec in module.lectures if lec.id in transcripts]
            if not module_lectures:
                continue

            lines.append(f"## {module.title}")
            lines.append("")

            for lecture in module_lectures:
                lines.append(f"### {lecture.title}")
                lines.append("")
                lines.append(transcripts[lecture.id])
                lines.append("")

        return "\n".join(lines)

    def save_extras(
        self,
        course_dir: Path,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Gera MOC e índices de módulo pro Obsidian."""
        self._save_moc(course_dir, modules, transcripts, course_title, slug)
        self._save_module_indexes(course_dir, modules, transcripts, course_title)
        print("   📝 MOC e índices de módulo gerados")

    def _save_moc(
        self,
        course_dir: Path,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
        slug: str,
    ) -> None:
        """Gera o Map of Content (MOC) do curso."""
        source_url = _build_source_url(self.platform, slug)

        lines = [
            "---",
            f'course: "{course_title}"',
            f"platform: {self.platform}",
            "type: moc",
            f"date: {date.today().isoformat()}",
            "tags:",
            f"  - {self.platform}",
            f"  - curso/{_slugify_tag(course_title)}",
            "  - moc",
            "---",
            "",
            f"# 🎓 {course_title}",
            "",
            "> [!info] Map of Content",
        ]
        if source_url:
            lines.append(f"> Curso: [{course_title}]({source_url})")
        lines.append("")

        total = sum(1 for lec_id in transcripts)
        lines.append(f"**{total} aulas transcritas** | {len(modules)} módulos")
        lines.append("")

        for module in modules:
            module_lectures = [lec for lec in module.lectures if lec.id in transcripts]
            if not module_lectures:
                continue

            module_dir = self.get_module_dirname(module)
            lines.append(f"## {module.title}")
            lines.append("")

            for lecture in module_lectures:
                fname = self.get_lecture_filename(lecture)
                link_target = f"{module_dir}/{fname}".removesuffix(".md")
                lines.append(f"- [[{link_target}|{lecture.title}]]")

            lines.append("")

        moc_path = course_dir / "_MOC.md"
        moc_path.write_text("\n".join(lines), encoding="utf-8")

    def _save_module_indexes(
        self,
        course_dir: Path,
        modules: list[Module],
        transcripts: dict[int | str, str],
        course_title: str,
    ) -> None:
        """Gera índice para cada módulo."""
        for module in modules:
            module_lectures = [lec for lec in module.lectures if lec.id in transcripts]
            if not module_lectures:
                continue

            module_dir = course_dir / self.get_module_dirname(module)
            module_dir.mkdir(exist_ok=True)

            lines = [
                "---",
                f'course: "{course_title}"',
                f'section: "{module.title}"',
                f"platform: {self.platform}",
                "tags:",
                f"  - {self.platform}",
                f"  - curso/{_slugify_tag(course_title)}",
                f"  - secao/{_slugify_tag(module.title)}",
                "---",
                "",
                f"# {module.title}",
                "",
                f"> [!abstract] Módulo {module.index} — {len(module_lectures)} aulas",
                "",
            ]

            for lecture in module_lectures:
                fname = self.get_lecture_filename(lecture).removesuffix(".md")
                lines.append(f"1. [[{fname}|{lecture.title}]]")

            lines.append("")

            index_path = module_dir / "_index.md"
            index_path.write_text("\n".join(lines), encoding="utf-8")


# ─── Helpers ────────────────────────────────────────────────────────────────


def _slugify_tag(text: str) -> str:
    """Converte texto em tag amigável para Obsidian.

    >>> _slugify_tag("Docker - Zero a Profissional")
    'docker-zero-a-profissional'
    """
    tag = text.lower().strip()
    tag = re.sub(r"[^\w\s-]", "", tag)
    tag = re.sub(r"[\s_]+", "-", tag)
    tag = re.sub(r"-+", "-", tag).strip("-")
    return tag


def _build_source_url(platform: str, slug: str) -> str | None:
    """Constrói URL pública do curso a partir da plataforma + slug.

    Retorna None pra DIO (sem URL pública estável por bootcamp).
    """
    templates = {
        "udemy": f"https://www.udemy.com/course/{slug}/",
        "alura": f"https://cursos.alura.com.br/course/{slug}",
    }
    return templates.get(platform)


def _build_nav_callout(
    current: Lecture,
    prev_lec: Lecture | None,
    next_lec: Lecture | None,
) -> str:
    parts = []
    if prev_lec:
        prev_name = f"{prev_lec.object_index:03d} - {sanitize_filename(prev_lec.title)}"
        parts.append(f"⬅ [[{prev_name}|Anterior]]")
    if next_lec:
        next_name = f"{next_lec.object_index:03d} - {sanitize_filename(next_lec.title)}"
        parts.append(f"[[{next_name}|Próxima]] ➡")

    if not parts:
        return ""
    nav_text = " | ".join(parts)
    return f"> [!tip] Navegação\n> {nav_text}"


def _split_into_paragraphs(text: str, sentences_per_paragraph: int = 4) -> list[str]:
    """Quebra texto corrido em parágrafos para melhor leitura no Obsidian."""
    if "\n" in text.strip():
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) <= sentences_per_paragraph:
        return [text]

    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        chunk = sentences[i : i + sentences_per_paragraph]
        paragraphs.append(" ".join(chunk))

    return paragraphs
