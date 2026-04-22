"""Testes do `DioSource` — amarra video_finder + whisper_engine."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from classroom_transcripter.core.models import Lecture, Transcript, TranscriptCue
from classroom_transcripter.sources.dio import DioSource


def test_source_name():
    assert DioSource().name == "dio"


def test_authenticate_is_noop():
    DioSource().authenticate()  # não deve lançar


def test_fetch_course_uses_video_finder(tmp_path):
    """fetch_course delega pra discover_course — estrutura profunda obrigatória."""
    bootcamp = tmp_path / "curso"
    mod = bootcamp / "01-modulo"
    mod.mkdir(parents=True)
    video = mod / "01-aula.mp4"
    video.write_bytes(b"fake")

    course = DioSource().fetch_course(str(bootcamp))
    assert course.platform == "dio"
    assert len(course.modules) == 1
    assert course.modules[0].lectures[0].metadata["file"] == str(video)


def test_fetch_transcript_delegates_to_whisper(tmp_path):
    video = tmp_path / "aula.mp4"
    video.write_bytes(b"fake")
    lec = Lecture(id=1, title="Aula", object_index=1, metadata={"file": str(video)})

    expected = Transcript(
        lecture_id=1,
        language="pt",
        plain_text="texto",
        cues=[TranscriptCue(0, 1, "texto")],
    )

    with patch(
        "classroom_transcripter.sources.dio.source.transcribe",
        return_value=expected,
    ) as mock_tx:
        result = DioSource(whisper_model="small", language="pt").fetch_transcript(lec)

    assert result is expected
    kwargs = mock_tx.call_args.kwargs
    assert kwargs["lecture_id"] == 1
    assert kwargs["model_name"] == "small"
    assert kwargs["language"] == "pt"


def test_fetch_transcript_passes_model_name(tmp_path):
    video = tmp_path / "aula.mp4"
    video.write_bytes(b"fake")
    lec = Lecture(id=1, title="A", object_index=1, metadata={"file": str(video)})

    with patch("classroom_transcripter.sources.dio.source.transcribe") as mock_tx:
        DioSource(whisper_model="medium").fetch_transcript(lec)
    assert mock_tx.call_args.kwargs["model_name"] == "medium"


# ─── Integração com downloader genérico ───────────────────────────────────


def test_dio_source_compatible_with_downloader(tmp_path):
    """Integração: DioSource + download_course produzem .md corretos."""
    from classroom_transcripter.core.downloader import download_course
    from classroom_transcripter.core.formatters import ObsidianFormatter

    bootcamp = tmp_path / "meu-bootcamp"
    mod = bootcamp / "01-intro"
    mod.mkdir(parents=True)
    (mod / "01-primeira.mp4").write_bytes(b"fake1")
    (mod / "02-segunda.mp4").write_bytes(b"fake2")

    source = DioSource()
    course = source.fetch_course(str(bootcamp))

    def fake_transcribe(media_path, *, lecture_id, **kwargs):
        return Transcript(
            lecture_id=lecture_id,
            language="pt",
            plain_text=f"Transcrição da aula {lecture_id}",
        )

    output = tmp_path / "out"
    with patch(
        "classroom_transcripter.sources.dio.source.transcribe",
        side_effect=fake_transcribe,
    ):
        result = download_course(
            source,
            course,
            output_dir=output,
            formatter=ObsidianFormatter(platform="dio"),
        )

    assert result.downloaded == 2
    assert result.platform == "dio"

    course_dir = Path(result.output_dir)
    file_1 = course_dir / "01 - Intro" / "001 - Primeira.md"
    assert file_1.exists()
    content = file_1.read_text(encoding="utf-8")
    assert "platform: dio" in content
    assert "Transcrição da aula" in content


def test_resume_works_with_dio(tmp_path):
    """--resume do downloader pula aulas que já têm .md gerado.

    Este é o motivo de NÃO ter cache em disco: --resume cobre retomada
    de execução interrompida.
    """
    from classroom_transcripter.core.downloader import download_course
    from classroom_transcripter.core.formatters import ObsidianFormatter

    bootcamp = tmp_path / "b"
    mod = bootcamp / "01-m"
    mod.mkdir(parents=True)
    (mod / "01-a.mp4").write_bytes(b"fake")
    (mod / "02-b.mp4").write_bytes(b"fake")

    source = DioSource()
    course = source.fetch_course(str(bootcamp))

    def fake_transcribe(media_path, *, lecture_id, **kwargs):
        return Transcript(
            lecture_id=lecture_id,
            language="pt",
            plain_text=f"t {lecture_id}",
        )

    output = tmp_path / "out"

    # Primeira execução — transcreve tudo
    with patch(
        "classroom_transcripter.sources.dio.source.transcribe",
        side_effect=fake_transcribe,
    ) as mock1:
        r1 = download_course(
            source, course, output_dir=output,
            formatter=ObsidianFormatter(platform="dio"),
        )
    assert r1.downloaded == 2
    assert mock1.call_count == 2

    # Segunda execução com --resume — pula tudo
    with patch(
        "classroom_transcripter.sources.dio.source.transcribe",
        side_effect=fake_transcribe,
    ) as mock2:
        r2 = download_course(
            source, course, output_dir=output, resume=True,
            formatter=ObsidianFormatter(platform="dio"),
        )
    assert r2.skipped == 2
    assert r2.downloaded == 0
    assert mock2.call_count == 0  # Whisper NÃO foi chamado
