"""Testes do `video_finder` — só estrutura profunda (subpastas por módulo)."""
from __future__ import annotations

from pathlib import Path

import pytest

from classroom_transcripter.core.exceptions import CourseNotFoundError
from classroom_transcripter.sources.dio.video_finder import (
    _natural_sort_key,
    _prettify_name,
    _slugify_dir_name,
    discover_course,
)


def _make_video(path: Path, name: str) -> Path:
    f = path / name
    f.write_bytes(b"fake mp4")
    return f


# ─── Estrutura profunda (única suportada) ──────────────────────────────────


def test_deep_structure_basic(tmp_path):
    bootcamp = tmp_path / "meu-bootcamp"
    mod1 = bootcamp / "01-fundamentos"
    mod1.mkdir(parents=True)
    _make_video(mod1, "01-introducao.mp4")
    _make_video(mod1, "02-variaveis.mp4")

    mod2 = bootcamp / "02-apis"
    mod2.mkdir()
    _make_video(mod2, "01-rest.mp4")

    course = discover_course(bootcamp)

    assert course.platform == "dio"
    assert len(course.modules) == 2
    assert course.modules[0].title == "Fundamentos"
    assert course.modules[1].title == "Apis"

    assert len(course.modules[0].lectures) == 2
    assert course.modules[0].lectures[0].title == "Introducao"
    assert course.modules[0].lectures[0].object_index == 1


def test_lectures_have_file_metadata(tmp_path):
    bootcamp = tmp_path / "b"
    mod = bootcamp / "01-m"
    mod.mkdir(parents=True)
    video = _make_video(mod, "01-aula.mp4")

    course = discover_course(bootcamp)
    lecture = course.modules[0].lectures[0]
    assert Path(lecture.metadata["file"]) == video


def test_natural_order_of_modules(tmp_path):
    """10-foo vem DEPOIS de 02-bar."""
    bootcamp = tmp_path / "b"
    (bootcamp / "02-segundo").mkdir(parents=True)
    _make_video(bootcamp / "02-segundo", "a.mp4")
    (bootcamp / "10-decimo").mkdir()
    _make_video(bootcamp / "10-decimo", "a.mp4")
    (bootcamp / "01-primeiro").mkdir()
    _make_video(bootcamp / "01-primeiro", "a.mp4")

    course = discover_course(bootcamp)
    titles = [m.title for m in course.modules]
    assert titles == ["Primeiro", "Segundo", "Decimo"]


def test_natural_order_of_lectures_within_module(tmp_path):
    bootcamp = tmp_path / "b"
    mod = bootcamp / "01-m"
    mod.mkdir(parents=True)
    _make_video(mod, "02-segunda.mp4")
    _make_video(mod, "10-decima.mp4")
    _make_video(mod, "01-primeira.mp4")

    course = discover_course(bootcamp)
    titles = [lec.title for lec in course.modules[0].lectures]
    assert titles == ["Primeira", "Segunda", "Decima"]


def test_skips_empty_module_dirs(tmp_path):
    """Subpasta sem vídeos é ignorada."""
    bootcamp = tmp_path / "b"
    (bootcamp / "01-com-video").mkdir(parents=True)
    _make_video(bootcamp / "01-com-video", "a.mp4")
    (bootcamp / "02-vazia").mkdir()

    course = discover_course(bootcamp)
    assert len(course.modules) == 1


def test_multiple_video_extensions(tmp_path):
    """Aceita .mp4, .mkv, .webm, .mp3, etc."""
    bootcamp = tmp_path / "b"
    mod = bootcamp / "01-m"
    mod.mkdir(parents=True)
    _make_video(mod, "a.mp4")
    _make_video(mod, "b.mkv")
    _make_video(mod, "c.webm")
    _make_video(mod, "d.mp3")

    course = discover_course(bootcamp)
    assert len(course.modules[0].lectures) == 4


def test_ignores_non_video_files(tmp_path):
    bootcamp = tmp_path / "b"
    mod = bootcamp / "01-m"
    mod.mkdir(parents=True)
    _make_video(mod, "a.mp4")
    (mod / "readme.txt").write_text("x")
    (mod / "_notes.md").write_text("x")

    course = discover_course(bootcamp)
    assert len(course.modules[0].lectures) == 1


def test_ignores_hidden_module_dirs(tmp_path):
    bootcamp = tmp_path / "b"
    (bootcamp / "01-visible").mkdir(parents=True)
    _make_video(bootcamp / "01-visible", "a.mp4")
    (bootcamp / ".hidden").mkdir()
    _make_video(bootcamp / ".hidden", "a.mp4")

    course = discover_course(bootcamp)
    assert len(course.modules) == 1


# ─── Erros ────────────────────────────────────────────────────────────────


def test_nonexistent_dir_raises(tmp_path):
    with pytest.raises(CourseNotFoundError, match="não encontrada"):
        discover_course(tmp_path / "nao-existe")


def test_dir_without_subdirs_raises(tmp_path):
    """Convenção exige subpastas — estrutura plana é ERRO."""
    flat = tmp_path / "plano"
    flat.mkdir()
    _make_video(flat, "01-aula.mp4")

    with pytest.raises(CourseNotFoundError, match="subpastas"):
        discover_course(flat)


def test_empty_dir_raises(tmp_path):
    empty = tmp_path / "vazio"
    empty.mkdir()
    with pytest.raises(CourseNotFoundError, match="subpastas"):
        discover_course(empty)


def test_subdirs_without_videos_raises(tmp_path):
    bootcamp = tmp_path / "b"
    (bootcamp / "mod1").mkdir(parents=True)
    (bootcamp / "mod2").mkdir()
    # nenhuma tem .mp4
    with pytest.raises(CourseNotFoundError, match="Nenhum vídeo"):
        discover_course(bootcamp)


# ─── Helpers internos ─────────────────────────────────────────────────────


def test_natural_sort_key_numeric():
    names = ["10-z.mp4", "01-a.mp4", "02-b.mp4"]
    assert sorted(names, key=_natural_sort_key) == ["01-a.mp4", "02-b.mp4", "10-z.mp4"]


def test_prettify_removes_numeric_prefix():
    assert _prettify_name("01-introducao") == "Introducao"
    assert _prettify_name("02 - apis") == "Apis"
    assert _prettify_name("03_banco_de_dados") == "Banco De Dados"


def test_prettify_handles_no_prefix():
    assert _prettify_name("jornada-node") == "Jornada Node"


def test_prettify_preserves_original_if_cleanup_empty():
    """Se depois de limpar sobrar nada, mantém o original."""
    assert _prettify_name("01") == "01"


def test_slugify():
    assert _slugify_dir_name("My Bootcamp") == "my-bootcamp"
    assert _slugify_dir_name("  Jornada   Node  ") == "jornada-node"
