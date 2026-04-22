"""Testes do downloader genérico usando FakeSource (sem HTTP)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from classroom_transcripter.core.downloader import (
    _build_lecture_navigation,
    _count_lectures_with_transcripts,
    _format_seconds,
    _transcript_to_text,
    download_by_identifier,
    download_course,
    list_available_captions,
)
from classroom_transcripter.core.exceptions import TranscriptNotAvailableError
from classroom_transcripter.core.formatters import ObsidianFormatter, PlainTextFormatter
from classroom_transcripter.core.models import (
    Caption,
    Course,
    Lecture,
    Module,
    Transcript,
    TranscriptCue,
)
from classroom_transcripter.sources.base import TranscriptSource


# ─── Fake source pra testar sem HTTP ─────────────────────────────────────


class FakeSource(TranscriptSource):
    """Implementa TranscriptSource em memória pra testar o downloader."""

    name = "fake"

    def __init__(self, transcripts: dict[int | str, Transcript] | None = None):
        self._transcripts = transcripts or {}
        self.authenticated = False
        self.fetch_course_calls: list[str] = []
        self.fetch_transcript_calls: list[int | str] = []

    def authenticate(self) -> None:
        self.authenticated = True

    def fetch_course(self, identifier: str) -> Course:
        self.fetch_course_calls.append(identifier)
        return Course(
            id=1, slug=identifier, title="Curso Teste", platform="fake",
            modules=[
                Module(title="Módulo 1", index=1, lectures=[
                    Lecture(id=1, title="Aula A", object_index=1,
                            captions=[Caption(locale="pt", url="u1", label="PT")]),
                ]),
            ],
        )

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        self.fetch_transcript_calls.append(lecture.id)
        if lecture.id not in self._transcripts:
            raise TranscriptNotAvailableError(f"fake: sem transcript pra {lecture.id}")
        return self._transcripts[lecture.id]


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def simple_course() -> Course:
    """Curso com 2 módulos, 3 aulas, todas com captions."""
    return Course(
        id=42, slug="curso-teste", title="Curso Teste", platform="fake",
        modules=[
            Module(title="Módulo 1", index=1, lectures=[
                Lecture(id=1, title="Aula A", object_index=1,
                        captions=[Caption(locale="pt", url="u", label="PT")]),
                Lecture(id=2, title="Aula B", object_index=2,
                        captions=[Caption(locale="pt", url="u", label="PT")]),
            ]),
            Module(title="Módulo 2", index=2, lectures=[
                Lecture(id=3, title="Aula C", object_index=1,
                        captions=[Caption(locale="pt", url="u", label="PT")]),
            ]),
        ],
    )


@pytest.fixture
def transcripts_map() -> dict[int | str, Transcript]:
    return {
        1: Transcript(lecture_id=1, language="pt", plain_text="texto A"),
        2: Transcript(lecture_id=2, language="pt", plain_text="texto B"),
        3: Transcript(lecture_id=3, language="pt", plain_text="texto C"),
    }


# ─── Helpers puros ────────────────────────────────────────────────────────


def test_format_seconds():
    assert _format_seconds(0) == "00:00:00"
    assert _format_seconds(65) == "00:01:05"
    assert _format_seconds(3661.5) == "01:01:01"


def test_count_lectures_with_captions():
    mods = [
        Module(title="M1", index=1, lectures=[
            Lecture(id=1, title="A", object_index=1,
                    captions=[Caption(locale="pt", url="u", label="P")]),
            Lecture(id=2, title="B", object_index=2),  # sem caption
        ]),
    ]
    assert _count_lectures_with_transcripts(mods) == 1


def test_count_lectures_with_dio_metadata():
    """DIO não tem captions mas tem metadata[file]."""
    mods = [
        Module(title="M", index=1, lectures=[
            Lecture(id=1, title="A", object_index=1, metadata={"file": "/tmp/x.mp4"}),
            Lecture(id=2, title="B", object_index=2, metadata={}),
        ]),
    ]
    assert _count_lectures_with_transcripts(mods) == 1


def test_nav_builds_prev_next_correctly(simple_course):
    nav = _build_lecture_navigation(simple_course.modules)
    # 3 lectures: 1 → 2 → 3
    assert nav[1] == (None, simple_course.modules[0].lectures[1])
    assert nav[2][0].id == 1
    assert nav[2][1].id == 3
    assert nav[3][1] is None


def test_nav_skips_unavailable_lectures():
    """Aulas sem caption/mp4 não entram na navegação (Obsidian não linka pra elas)."""
    mods = [
        Module(title="M", index=1, lectures=[
            Lecture(id=1, title="A", object_index=1,
                    captions=[Caption(locale="pt", url="u", label="P")]),
            Lecture(id=2, title="B", object_index=2),  # sem caption
            Lecture(id=3, title="C", object_index=3,
                    captions=[Caption(locale="pt", url="u", label="P")]),
        ]),
    ]
    nav = _build_lecture_navigation(mods)
    assert 2 not in nav
    # 1 → 3 (pula 2)
    assert nav[1][1].id == 3


def test_transcript_to_text_plain_text():
    t = Transcript(lecture_id=1, language="pt", plain_text="texto corrido")
    assert _transcript_to_text(t, with_timestamps=False) == "texto corrido"


def test_transcript_to_text_timestamps():
    t = Transcript(
        lecture_id=1, language="pt",
        cues=[
            TranscriptCue(start_seconds=1.0, end_seconds=2.0, text="olá"),
            TranscriptCue(start_seconds=3.0, end_seconds=4.0, text="mundo"),
        ],
    )
    out = _transcript_to_text(t, with_timestamps=True)
    assert "[00:00:01] olá" in out
    assert "[00:00:03] mundo" in out


def test_transcript_to_text_fallback_from_cues():
    """Sem plain_text mas com cues → junta cues."""
    t = Transcript(
        lecture_id=1, language="pt",
        cues=[TranscriptCue(0, 1, "a"), TranscriptCue(1, 2, "b")],
    )
    assert _transcript_to_text(t, with_timestamps=False) == "a b"


# ─── download_course — fluxo feliz ────────────────────────────────────────


def test_download_course_writes_all_files(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    result = download_course(
        source, simple_course,
        output_dir=tmp_path,
        formatter=PlainTextFormatter(),
    )

    assert result.downloaded == 3
    assert result.errors == 0
    assert result.total_modules == 2
    assert result.platform == "fake"

    # Estrutura criada no disco
    course_dir = Path(result.output_dir)
    assert (course_dir / "01 - Módulo 1" / "001 - Aula A.txt").exists()
    assert (course_dir / "01 - Módulo 1" / "002 - Aula B.txt").exists()
    assert (course_dir / "02 - Módulo 2" / "001 - Aula C.txt").exists()


def test_download_course_writes_metadata(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    result = download_course(source, simple_course, output_dir=tmp_path)

    meta_path = Path(result.output_dir) / "_metadata.json"
    assert meta_path.exists()

    meta = json.loads(meta_path.read_text())
    assert meta["platform"] == "fake"
    assert meta["course_id"] == 42
    assert meta["total_lectures"] == 3
    assert meta["transcribed"] == 3


def test_download_course_file_contents(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    download_course(source, simple_course, output_dir=tmp_path)

    file_a = tmp_path / "Curso Teste" / "01 - Módulo 1" / "001 - Aula A.txt"
    assert file_a.read_text(encoding="utf-8") == "texto A"


# ─── Merge ────────────────────────────────────────────────────────────────


def test_download_with_merge_creates_full_file(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    download_course(source, simple_course, output_dir=tmp_path, merge=True)

    merged = tmp_path / "Curso Teste" / "_CURSO_COMPLETO.txt"
    assert merged.exists()
    content = merged.read_text()
    assert "texto A" in content
    assert "texto B" in content
    assert "texto C" in content


# ─── Resume ───────────────────────────────────────────────────────────────


def test_resume_skips_existing_files(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    # Primeira execução
    download_course(source, simple_course, output_dir=tmp_path)

    # Segunda com resume — não deve chamar fetch_transcript de novo
    source2 = FakeSource(transcripts_map)
    result = download_course(source2, simple_course, output_dir=tmp_path, resume=True)

    assert result.skipped == 3
    assert result.downloaded == 0
    assert source2.fetch_transcript_calls == []  # nenhuma chamada feita


# ─── Erros ────────────────────────────────────────────────────────────────


def test_download_raises_when_no_lectures_available(tmp_path):
    """Curso sem nenhuma caption → TranscriptNotAvailableError."""
    empty_course = Course(
        id=1, slug="x", title="Vazio", platform="fake",
        modules=[Module(title="M", index=1, lectures=[
            Lecture(id=1, title="Sem caption", object_index=1),
        ])],
    )
    with pytest.raises(TranscriptNotAvailableError):
        download_course(FakeSource(), empty_course, output_dir=tmp_path)


def test_download_continues_on_individual_errors(tmp_path, simple_course):
    """Se UMA aula falha, continua e conta como erro."""
    # Source tem transcript só pras aulas 1 e 3 — aula 2 vai lançar
    source = FakeSource({
        1: Transcript(lecture_id=1, language="pt", plain_text="A"),
        3: Transcript(lecture_id=3, language="pt", plain_text="C"),
    })
    result = download_course(source, simple_course, output_dir=tmp_path)

    assert result.downloaded == 2
    assert result.errors == 1


# ─── download_by_identifier ───────────────────────────────────────────────


def test_download_by_identifier_calls_fetch_course(tmp_path):
    source = FakeSource({
        1: Transcript(lecture_id=1, language="pt", plain_text="x"),
    })
    result = download_by_identifier(source, "meu-curso-slug", output_dir=tmp_path)

    assert source.fetch_course_calls == ["meu-curso-slug"]
    assert result.slug == "meu-curso-slug"
    assert result.downloaded == 1


# ─── list_available_captions ──────────────────────────────────────────────


def test_list_available_captions_returns_dict(simple_course):
    langs = list_available_captions(FakeSource(), simple_course)
    assert "pt" in langs
    assert langs["pt"]["count"] == 3
    assert langs["pt"]["label"] == "PT"


def test_list_available_captions_empty_course():
    course = Course(
        id=1, slug="x", title="X", platform="fake",
        modules=[Module(title="M", index=1, lectures=[
            Lecture(id=1, title="A", object_index=1),  # sem captions
        ])],
    )
    langs = list_available_captions(FakeSource(), course)
    assert langs == {}


# ─── Formatter integration ────────────────────────────────────────────────


def test_download_with_obsidian_creates_moc(tmp_path, simple_course, transcripts_map):
    """ObsidianFormatter.save_extras gera _MOC.md + _index.md por módulo."""
    source = FakeSource(transcripts_map)
    download_course(
        source, simple_course,
        output_dir=tmp_path,
        formatter=ObsidianFormatter(platform="fake"),
    )

    course_dir = tmp_path / "Curso Teste"
    assert (course_dir / "_MOC.md").exists()
    assert (course_dir / "01 - Módulo 1" / "_index.md").exists()
    assert (course_dir / "02 - Módulo 2" / "_index.md").exists()


def test_obsidian_files_have_platform_frontmatter(tmp_path, simple_course, transcripts_map):
    source = FakeSource(transcripts_map)
    download_course(
        source, simple_course,
        output_dir=tmp_path,
        formatter=ObsidianFormatter(platform="fake"),
    )

    file_a = tmp_path / "Curso Teste" / "01 - Módulo 1" / "001 - Aula A.md"
    content = file_a.read_text(encoding="utf-8")
    assert "platform: fake" in content
    assert "- fake" in content  # tag dinâmica
