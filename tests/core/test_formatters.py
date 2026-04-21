"""Testes dos formatters (txt + obsidian)."""
import pytest

from classroom_transcripter.core.formatters import (
    FORMATTERS,
    ObsidianFormatter,
    PlainTextFormatter,
    get_formatter,
)
from classroom_transcripter.core.models import Lecture, Module


@pytest.fixture
def sample_lecture():
    return Lecture(id=1, title="Introdução ao Docker", object_index=1)


@pytest.fixture
def sample_module():
    return Module(title="Módulo 1", index=1)


# ─── Factory ───────────────────────────────────────────────────────────────


def test_get_formatter_txt():
    assert isinstance(get_formatter("txt"), PlainTextFormatter)


def test_get_formatter_obsidian():
    assert isinstance(get_formatter("obsidian"), ObsidianFormatter)


def test_get_formatter_unknown_raises():
    with pytest.raises(ValueError, match="não encontrado"):
        get_formatter("notion")


def test_formatters_registry_keys():
    assert "txt" in FORMATTERS
    assert "obsidian" in FORMATTERS


# ─── PlainTextFormatter ────────────────────────────────────────────────────


def test_txt_extension():
    assert PlainTextFormatter().file_extension() == ".txt"


def test_txt_format_lecture_returns_transcript_as_is(sample_lecture, sample_module):
    f = PlainTextFormatter()
    out = f.format_lecture(
        lecture=sample_lecture,
        module=sample_module,
        transcript="conteúdo bruto da aula",
        course_title="Docker",
        slug="docker",
    )
    assert out == "conteúdo bruto da aula"


def test_txt_get_lecture_filename(sample_lecture):
    name = PlainTextFormatter().get_lecture_filename(sample_lecture)
    assert name == "001 - Introdução ao Docker.txt"


def test_txt_get_module_dirname(sample_module):
    name = PlainTextFormatter().get_module_dirname(sample_module)
    assert name == "01 - Módulo 1"


# ─── ObsidianFormatter ─────────────────────────────────────────────────────


def test_obsidian_extension():
    assert ObsidianFormatter().file_extension() == ".md"


def test_obsidian_default_platform_is_udemy():
    """Compat v0.1: sem arg → platform=udemy."""
    out = ObsidianFormatter().format_lecture(
        lecture=Lecture(id=1, title="X", object_index=1),
        module=Module(title="M", index=1),
        transcript="t",
        course_title="C",
        slug="c",
    )
    assert "platform: udemy" in out
    assert "- udemy" in out  # tag


def test_obsidian_custom_platform_flows_into_frontmatter():
    """v0.2: platform=dio → frontmatter e tag mudam."""
    out = ObsidianFormatter(platform="dio").format_lecture(
        lecture=Lecture(id=1, title="X", object_index=1),
        module=Module(title="M", index=1),
        transcript="t",
        course_title="C",
        slug="c",
    )
    assert "platform: dio" in out
    assert "- dio" in out
    assert "dio_id: 1" in out  # frontmatter usa nome dinâmico


def test_obsidian_lecture_has_frontmatter_delimiters():
    out = ObsidianFormatter().format_lecture(
        lecture=Lecture(id=1, title="Aula", object_index=1),
        module=Module(title="M", index=1),
        transcript="texto",
        course_title="Curso",
        slug="curso",
    )
    # Começa e termina o frontmatter com ---
    assert out.startswith("---\n")
    assert out.count("---") >= 2


def test_obsidian_has_anotacoes_section():
    out = ObsidianFormatter().format_lecture(
        lecture=Lecture(id=1, title="X", object_index=1),
        module=Module(title="M", index=1),
        transcript="t",
        course_title="C",
        slug="c",
    )
    assert "## Anotações" in out


def test_obsidian_merge_has_all_modules_with_transcripts():
    mods = [
        Module(title="M1", index=1, lectures=[Lecture(id=1, title="A", object_index=1)]),
        Module(title="M2", index=2, lectures=[Lecture(id=2, title="B", object_index=1)]),
    ]
    transcripts = {1: "texto A", 2: "texto B"}
    out = ObsidianFormatter().format_merged(
        modules=mods, transcripts=transcripts, course_title="Curso", total_downloaded=2,
    )
    assert "## M1" in out
    assert "## M2" in out
    assert "texto A" in out
    assert "texto B" in out


def test_obsidian_merge_skips_modules_without_transcripts():
    mods = [
        Module(title="Vazio", index=1, lectures=[Lecture(id=999, title="X", object_index=1)]),
        Module(title="Cheio", index=2, lectures=[Lecture(id=1, title="A", object_index=1)]),
    ]
    transcripts = {1: "texto"}
    out = ObsidianFormatter().format_merged(
        modules=mods, transcripts=transcripts, course_title="C", total_downloaded=1,
    )
    assert "## Vazio" not in out
    assert "## Cheio" in out
