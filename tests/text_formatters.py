"""Testes dos formatadores de saída."""

import pytest

from udemy_transcripter.formatters import (
    ObsidianFormatter,
    PlainTextFormatter,
    _slugify_tag,
    _split_into_paragraphs,
    get_formatter,
)
from udemy_transcripter.models import Caption, Lecture, Section

# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_lecture(index: int = 1, title: str = "Aula Teste") -> Lecture:
    return Lecture(
        id=100 + index,
        title=title,
        object_index=index,
        captions=[Caption(locale="pt_BR", url="http://x.vtt", label="Português")],
    )


def _make_section(index: int = 1, title: str = "Seção Teste") -> Section:
    return Section(title=title, index=index, lectures=[_make_lecture()])


# ─── Registry ──────────────────────────────────────────────────────────────


class TestGetFormatter:
    def test_txt(self):
        fmt = get_formatter("txt")
        assert isinstance(fmt, PlainTextFormatter)

    def test_obsidian(self):
        fmt = get_formatter("obsidian")
        assert isinstance(fmt, ObsidianFormatter)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="não encontrado"):
            get_formatter("notion")


# ─── PlainTextFormatter ────────────────────────────────────────────────────


class TestPlainTextFormatter:
    def test_extension(self):
        assert PlainTextFormatter().file_extension() == ".txt"

    def test_format_lecture_returns_transcript_as_is(self):
        fmt = PlainTextFormatter()
        result = fmt.format_lecture(
            lecture=_make_lecture(),
            section=_make_section(),
            transcript="Texto da aula.",
            course_title="Curso",
            slug="curso",
        )
        assert result == "Texto da aula."

    def test_format_merged(self):
        fmt = PlainTextFormatter()
        section = _make_section()
        lec = section.lectures[0]
        result = fmt.format_merged(
            sections=[section],
            transcripts={lec.id: "Conteúdo."},
            course_title="Meu Curso",
            total_downloaded=1,
        )
        assert "Meu Curso" in result
        assert "Conteúdo." in result


# ─── ObsidianFormatter ─────────────────────────────────────────────────────


class TestObsidianFormatter:
    def test_extension(self):
        assert ObsidianFormatter().file_extension() == ".md"

    def test_format_lecture_has_frontmatter(self):
        fmt = ObsidianFormatter()
        result = fmt.format_lecture(
            lecture=_make_lecture(1, "Introdução ao Docker"),
            section=_make_section(1, "Começando"),
            transcript="Docker é uma plataforma de containers.",
            course_title="Docker Completo",
            slug="docker-completo",
        )
        assert result.startswith("---")
        assert "course: \"Docker Completo\"" in result
        assert "section: \"Começando\"" in result
        assert "tags:" in result
        assert "  - udemy" in result
        assert "# Introdução ao Docker" in result

    def test_format_lecture_has_transcript_section(self):
        fmt = ObsidianFormatter()
        result = fmt.format_lecture(
            lecture=_make_lecture(),
            section=_make_section(),
            transcript="Conteúdo da aula.",
            course_title="Curso",
            slug="curso",
        )
        assert "## Transcrição" in result
        assert "Conteúdo da aula." in result

    def test_format_lecture_has_notes_section(self):
        fmt = ObsidianFormatter()
        result = fmt.format_lecture(
            lecture=_make_lecture(),
            section=_make_section(),
            transcript="Texto.",
            course_title="Curso",
            slug="curso",
        )
        assert "## Anotações" in result

    def test_nav_links(self):
        fmt = ObsidianFormatter()
        prev_lec = _make_lecture(1, "Anterior")
        next_lec = _make_lecture(3, "Próxima")
        result = fmt.format_lecture(
            lecture=_make_lecture(2, "Atual"),
            section=_make_section(),
            transcript="Texto.",
            course_title="Curso",
            slug="curso",
            prev_lecture=prev_lec,
            next_lecture=next_lec,
        )
        assert "[[001 - Anterior|Anterior]]" in result
        assert "[[003 - Próxima|Próxima]]" in result

    def test_format_merged(self):
        fmt = ObsidianFormatter()
        section = _make_section()
        lec = section.lectures[0]
        result = fmt.format_merged(
            sections=[section],
            transcripts={lec.id: "Conteúdo."},
            course_title="Docker Completo",
            total_downloaded=1,
        )
        assert result.startswith("---")
        assert "# Docker Completo" in result
        assert "Conteúdo." in result

    def test_save_extras_creates_moc(self, tmp_path):
        fmt = ObsidianFormatter()
        section = _make_section()
        lec = section.lectures[0]
        fmt.save_extras(
            course_dir=tmp_path,
            sections=[section],
            transcripts={lec.id: "Texto."},
            course_title="Docker",
            slug="docker",
        )
        moc = tmp_path / "_MOC.md"
        assert moc.exists()
        content = moc.read_text()
        assert "🎓 Docker" in content
        assert "[[" in content  # Tem wikilinks

    def test_save_extras_creates_section_index(self, tmp_path):
        fmt = ObsidianFormatter()
        section = _make_section()
        lec = section.lectures[0]

        section_dir = tmp_path / fmt.get_section_dirname(section)
        section_dir.mkdir()

        fmt.save_extras(
            course_dir=tmp_path,
            sections=[section],
            transcripts={lec.id: "Texto."},
            course_title="Docker",
            slug="docker",
        )
        index = section_dir / "_index.md"
        assert index.exists()
        assert "Seção Teste" in index.read_text()


# ─── Helpers ────────────────────────────────────────────────────────────────


class TestSlugifyTag:
    def test_basic(self):
        assert _slugify_tag("Docker - Zero a Profissional") == "docker-zero-a-profissional"

    def test_special_chars(self):
        assert _slugify_tag("C# para .NET") == "c-para-net"

    def test_extra_spaces(self):
        assert _slugify_tag("  Muitos   Espaços  ") == "muitos-espaços"


class TestSplitIntoParagraphs:
    def test_short_text_unchanged(self):
        text = "Uma frase. Duas frases."
        result = _split_into_paragraphs(text)
        assert result == [text]

    def test_long_text_split(self):
        text = "Frase um. Frase dois. Frase três. Frase quatro. Frase cinco."
        result = _split_into_paragraphs(text, sentences_per_paragraph=2)
        assert len(result) == 3

    def test_timestamped_text_preserved(self):
        text = "[00:00:01] Linha 1\n[00:00:05] Linha 2"
        result = _split_into_paragraphs(text)
        assert result == [text]