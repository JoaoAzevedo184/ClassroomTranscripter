"""Testes dos modelos de domínio (Fase 2)."""
from classroom_transcripter.core.models import (
    Caption,
    Course,
    DownloadResult,
    Lecture,
    Module,
    Transcript,
    TranscriptCue,
)


def test_caption_dataclass():
    c = Caption(locale="pt", url="https://x.vtt", label="Português")
    assert c.locale == "pt"
    assert c.url == "https://x.vtt"


def test_lecture_defaults():
    lec = Lecture(id=1, title="Aula 1", object_index=1)
    assert lec.captions == []
    assert lec.metadata == {}


def test_lecture_with_captions():
    lec = Lecture(
        id=1, title="Aula 1", object_index=1,
        captions=[Caption(locale="pt", url="u1", label="PT")],
    )
    assert len(lec.captions) == 1
    assert lec.captions[0].locale == "pt"


def test_module_defaults():
    m = Module(title="Módulo 1", index=1)
    assert m.lectures == []


def test_course_iter_lectures_ordering():
    course = Course(
        id=42, slug="curso", title="Curso", platform="udemy",
        modules=[
            Module(title="M1", index=1, lectures=[
                Lecture(id=1, title="A", object_index=1),
                Lecture(id=2, title="B", object_index=2),
            ]),
            Module(title="M2", index=2, lectures=[
                Lecture(id=3, title="C", object_index=1),
            ]),
        ],
    )
    ids = [lec.id for lec in course.iter_lectures()]
    assert ids == [1, 2, 3]


def test_transcript_with_cues_has_timestamps():
    t = Transcript(
        lecture_id=1, language="pt",
        cues=[TranscriptCue(start_seconds=0.0, end_seconds=2.5, text="olá")],
    )
    assert t.has_timestamps is True


def test_transcript_plain_text_only():
    t = Transcript(lecture_id=1, language="pt", plain_text="texto")
    assert t.has_timestamps is False
    assert t.plain_text == "texto"


def test_download_result_has_platform_field():
    """v0.2 adicionou `platform` ao DownloadResult."""
    r = DownloadResult(
        course_title="X", course_id=1, slug="x", platform="udemy",
        total_modules=2, total_lectures=10, downloaded=8,
        errors=1, output_dir="/tmp/x",
    )
    assert r.platform == "udemy"
    assert r.skipped == 0  # default
