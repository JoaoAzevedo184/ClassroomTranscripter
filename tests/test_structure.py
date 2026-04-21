"""Sanity test da Fase 1: valida que o esqueleto foi montado corretamente.

Este teste NÃO exercita lógica de negócio (que ainda não foi migrada). Ele só
garante que:
  1. Todos os módulos planejados existem e importam sem erro
  2. As ABCs (TranscriptSource, BaseFormatter, AIProvider) estão bem definidas
  3. Os modelos de domínio (core/models.py) estão funcionais
  4. A hierarquia de exceções está consistente

Se esse teste passa, a Fase 1 tá concluída e podemos começar a Fase 2 com
confiança de que a casa tá estruturalmente ok.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# 1. Todos os módulos planejados importam
# ---------------------------------------------------------------------------

PLANNED_MODULES = [
    # Raiz
    "classroom_transcripter",
    # Core
    "classroom_transcripter.core",
    "classroom_transcripter.core.models",
    "classroom_transcripter.core.exceptions",
    "classroom_transcripter.core.config",
    "classroom_transcripter.core.utils",
    "classroom_transcripter.core.vtt",
    "classroom_transcripter.core.formatters",
    "classroom_transcripter.core.formatters.base",
    "classroom_transcripter.core.formatters.txt",
    "classroom_transcripter.core.formatters.obsidian",
    "classroom_transcripter.core.enricher",
    "classroom_transcripter.core.enricher.base",
    "classroom_transcripter.core.enricher.pipeline",
    "classroom_transcripter.core.enricher.providers",
    "classroom_transcripter.core.enricher.providers.groq",
    "classroom_transcripter.core.enricher.providers.gemini",
    "classroom_transcripter.core.enricher.providers.ollama",
    "classroom_transcripter.core.enricher.providers.claude",
    # Sources
    "classroom_transcripter.sources",
    "classroom_transcripter.sources.base",
    "classroom_transcripter.sources.udemy",
    "classroom_transcripter.sources.udemy.source",
    "classroom_transcripter.sources.udemy.client",
    "classroom_transcripter.sources.udemy.parser",
    "classroom_transcripter.sources.dio",
    "classroom_transcripter.sources.dio.source",
    "classroom_transcripter.sources.dio.whisper_engine",
    "classroom_transcripter.sources.dio.video_finder",
    "classroom_transcripter.sources.alura",
    "classroom_transcripter.sources.alura.source",
    "classroom_transcripter.sources.alura.client",
    "classroom_transcripter.sources.alura.parser",
    # CLI
    "classroom_transcripter.cli",
    "classroom_transcripter.cli.main",
    "classroom_transcripter.cli.udemy_cli",
    "classroom_transcripter.cli.dio_cli",
    "classroom_transcripter.cli.alura_cli",
    "classroom_transcripter.cli.enrich_cli",
]


@pytest.mark.parametrize("module_name", PLANNED_MODULES)
def test_module_imports(module_name: str) -> None:
    """Cada módulo planejado deve importar sem erro."""
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# 2. Modelos de domínio funcionais
# ---------------------------------------------------------------------------

def test_create_transcript_with_cues() -> None:
    from classroom_transcripter.core.models import Transcript, TranscriptCue

    t = Transcript(
        lecture_id="lec-1",
        language="pt",
        cues=[TranscriptCue(start_seconds=0.0, end_seconds=2.5, text="Olá")],
    )
    assert t.has_timestamps is True
    assert t.cues[0].text == "Olá"


def test_create_transcript_plain_text() -> None:
    from classroom_transcripter.core.models import Transcript

    t = Transcript(lecture_id="lec-1", language="pt", plain_text="texto corrido")
    assert t.has_timestamps is False
    assert t.plain_text == "texto corrido"


def test_course_iter_lectures_preserves_module_order() -> None:
    from classroom_transcripter.core.models import Course, Lecture, Module

    course = Course(
        id="c1",
        slug="meu-curso",
        title="Meu Curso",
        platform="udemy",
        modules=[
            Module(
                title="Módulo 1", index=1,
                lectures=[
                    Lecture(id="l1", title="A", object_index=1),
                    Lecture(id="l2", title="B", object_index=2),
                ],
            ),
            Module(
                title="Módulo 2", index=2,
                lectures=[Lecture(id="l3", title="C", object_index=1)],
            ),
        ],
    )
    ids = [lec.id for lec in course.iter_lectures()]
    assert ids == ["l1", "l2", "l3"]


# ---------------------------------------------------------------------------
# 3. Hierarquia de exceções
# ---------------------------------------------------------------------------

def test_exception_hierarchy() -> None:
    from classroom_transcripter.core.exceptions import (
        AccessDeniedError,
        AuthenticationError,
        ConfigurationError,
        CourseNotFoundError,
        NetworkError,
        ParseError,
        ProviderAPIKeyMissingError,
        ProviderError,
        RateLimitError,
        TranscripterError,
        TranscriptNotAvailableError,
    )

    # Todos herdam da raiz
    for exc in (
        AuthenticationError, AccessDeniedError, NetworkError, RateLimitError,
        CourseNotFoundError, TranscriptNotAvailableError, ParseError,
        ConfigurationError, ProviderError,
    ):
        assert issubclass(exc, TranscripterError), f"{exc.__name__} deve herdar de TranscripterError"

    # RateLimitError é também NetworkError
    assert issubclass(RateLimitError, NetworkError)

    # ProviderAPIKeyMissingError é ambos
    assert issubclass(ProviderAPIKeyMissingError, ProviderError)
    assert issubclass(ProviderAPIKeyMissingError, ConfigurationError)


# ---------------------------------------------------------------------------
# 4. ABCs: TranscriptSource não deve ser instanciável diretamente
# ---------------------------------------------------------------------------

def test_transcript_source_is_abstract() -> None:
    from classroom_transcripter.sources.base import TranscriptSource

    with pytest.raises(TypeError):
        TranscriptSource()  # type: ignore[abstract]


def test_base_formatter_is_abstract() -> None:
    from classroom_transcripter.core.formatters.base import BaseFormatter

    with pytest.raises(TypeError):
        BaseFormatter()  # type: ignore[abstract]


def test_ai_provider_is_abstract() -> None:
    from classroom_transcripter.core.enricher.base import AIProvider

    with pytest.raises(TypeError):
        AIProvider()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# 5. Sources concretos declaram os métodos (mesmo que com NotImplementedError)
# ---------------------------------------------------------------------------

def test_sources_declare_required_methods() -> None:
    from classroom_transcripter.sources.alura import AluraSource
    from classroom_transcripter.sources.dio import DioSource
    from classroom_transcripter.sources.udemy import UdemySource

    # Instanciar com args mínimos deve funcionar (só validando que a interface tá lá)
    for cls, kwargs in [
        (UdemySource, {"cookie": "x"}),
        (DioSource, {}),
        (AluraSource, {"email": "e@e.com", "password": "p"}),
    ]:
        src = cls(**kwargs)
        assert src.name in {"udemy", "dio", "alura"}
        # Métodos abstratos foram "implementados" (mesmo que stubs)
        assert callable(src.authenticate)
        assert callable(src.fetch_course)
        assert callable(src.fetch_transcript)
        assert callable(src.iter_lectures)


# ---------------------------------------------------------------------------
# 6. Factory de providers existe e valida nomes
# ---------------------------------------------------------------------------

def test_create_provider_rejects_unknown() -> None:
    from classroom_transcripter.core.enricher import create_provider

    with pytest.raises(ValueError):
        create_provider("inexistente")


# ---------------------------------------------------------------------------
# 7. Factory de formatters
# ---------------------------------------------------------------------------

def test_get_formatter_returns_correct_class() -> None:
    from classroom_transcripter.core.formatters import (
        ObsidianFormatter,
        PlainTextFormatter,
        get_formatter,
    )

    assert isinstance(get_formatter("txt"), PlainTextFormatter)
    assert isinstance(get_formatter("obsidian"), ObsidianFormatter)

    with pytest.raises(ValueError):
        get_formatter("inexistente")


# ---------------------------------------------------------------------------
# 8. CLI umbrella imprime ajuda sem crashar
# ---------------------------------------------------------------------------

def test_cli_main_help(capsys: pytest.CaptureFixture[str]) -> None:
    from classroom_transcripter.cli.main import main

    import sys
    old_argv = sys.argv
    sys.argv = ["classroom", "--help"]
    try:
        rc = main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert rc == 0
    assert "classroom" in captured.out.lower()
    assert "udemy" in captured.out
    assert "dio" in captured.out
    assert "alura" in captured.out


def test_cli_main_unknown_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    from classroom_transcripter.cli.main import main

    import sys
    old_argv = sys.argv
    sys.argv = ["classroom", "coursera"]  # não existe
    try:
        rc = main()
    finally:
        sys.argv = old_argv

    assert rc == 2


# ---------------------------------------------------------------------------
# 9. Smoke do versionamento
# ---------------------------------------------------------------------------

def test_version_declared() -> None:
    import classroom_transcripter

    assert hasattr(classroom_transcripter, "__version__")
    assert classroom_transcripter.__version__.startswith("0.")


# ---------------------------------------------------------------------------
# 10. Estrutura física mínima
# ---------------------------------------------------------------------------

def test_project_has_essential_files() -> None:
    """Confere que os arquivos-chave do projeto existem no disco."""
    import classroom_transcripter

    pkg_root = Path(classroom_transcripter.__file__).parent
    project_root = pkg_root.parent.parent  # sai de src/classroom_transcripter/

    essentials = [
        project_root / "pyproject.toml",
        project_root / "docs" / "arquitetura.md",
        project_root / "docs" / "refactor-plan.md",
    ]
    for p in essentials:
        assert p.exists(), f"Arquivo essencial faltando: {p}"
