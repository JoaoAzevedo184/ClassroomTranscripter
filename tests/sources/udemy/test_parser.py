"""Testes do helper `build_course` do parser Udemy."""
from classroom_transcripter.core.models import Lecture, Module
from classroom_transcripter.sources.udemy.parser import build_course


def test_build_course_sets_platform_udemy():
    c = build_course(course_id=1, title="X", slug="x", modules=[])
    assert c.platform == "udemy"


def test_build_course_fields():
    mods = [Module(title="M", index=1, lectures=[Lecture(id=1, title="A", object_index=1)])]
    c = build_course(course_id=42, title="Curso", slug="curso", modules=mods, language="pt")

    assert c.id == 42
    assert c.title == "Curso"
    assert c.slug == "curso"
    assert c.language == "pt"
    assert c.modules == mods
    assert c.metadata == {"api": "udemy"}


def test_build_course_language_optional():
    c = build_course(course_id=1, title="X", slug="x", modules=[])
    assert c.language is None
