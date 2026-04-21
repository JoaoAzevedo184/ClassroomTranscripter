"""Testes do enricher (pipeline + factory + base, sem chamar APIs de verdade)."""
from pathlib import Path

import pytest

from classroom_transcripter.core.enricher import (
    LLMProvider,
    create_provider,
    enrich_directory,
    enrich_file,
    is_enriched,
)
from classroom_transcripter.core.enricher.pipeline import (
    _extract_frontmatter,
    _extract_metadata_from_frontmatter,
)


# ─── Fake provider pra testar pipeline sem HTTP ───────────────────────────


class FakeProvider(LLMProvider):
    """Provider que devolve conteúdo fixo pra testar a pipeline."""

    def __init__(self, response: str = "CONTEÚDO ENRIQUECIDO"):
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def name(self) -> str:
        return "fake/test"

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.response


# ─── is_enriched ──────────────────────────────────────────────────────────


def test_is_enriched_detects_marker():
    assert is_enriched("conteúdo\n<!-- enriched-by: groq/x -->")


def test_is_enriched_returns_false_for_plain():
    assert not is_enriched("conteúdo sem marker")


# ─── Frontmatter ──────────────────────────────────────────────────────────


def test_extract_frontmatter_with_yaml():
    content = '---\ncourse: "X"\n---\n\n# Aula\n\nconteúdo'
    fm, body = _extract_frontmatter(content)
    assert fm.startswith("---")
    assert fm.endswith("---")
    assert 'course: "X"' in fm
    assert "# Aula" in body


def test_extract_frontmatter_without_yaml():
    fm, body = _extract_frontmatter("# Só conteúdo\n\ntexto")
    assert fm == ""
    assert body.startswith("# Só conteúdo")


def test_extract_metadata_parses_course_section():
    fm = '---\ncourse: "Docker"\nsection: "Fundamentos"\nother: x\n---'
    meta = _extract_metadata_from_frontmatter(fm)
    assert meta == {"course": "Docker", "section": "Fundamentos"}


# ─── enrich_file ──────────────────────────────────────────────────────────


def test_enrich_file_skips_already_enriched(tmp_path: Path):
    f = tmp_path / "aula.md"
    f.write_text("conteúdo\n<!-- enriched-by: groq/x -->\n")
    result = enrich_file(f, FakeProvider())
    assert result is False


def test_enrich_file_skips_underscore_files(tmp_path: Path):
    f = tmp_path / "_MOC.md"
    f.write_text("# MOC\n")
    result = enrich_file(f, FakeProvider())
    assert result is False


def test_enrich_file_dry_run_doesnt_modify(tmp_path: Path):
    f = tmp_path / "aula.md"
    original = '---\ncourse: "X"\n---\n\n# Aula 1\n\ntexto'
    f.write_text(original)
    result = enrich_file(f, FakeProvider(), dry_run=True)
    assert result is True
    assert f.read_text() == original  # não alterou


def test_enrich_file_writes_and_adds_marker(tmp_path: Path):
    f = tmp_path / "aula.md"
    f.write_text('---\ncourse: "X"\nsection: "S"\n---\n\n# Aula 1\n\ntexto')
    provider = FakeProvider(response='---\ncourse: "X"\n---\n\n# 📚 Visão Geral')
    enrich_file(f, provider)
    out = f.read_text()
    assert "<!-- enriched-by: fake/test -->" in out
    assert is_enriched(out)


def test_enrich_file_preserves_frontmatter_if_llm_drops_it(tmp_path: Path):
    f = tmp_path / "aula.md"
    fm = '---\ncourse: "X"\nsection: "S"\n---'
    f.write_text(f'{fm}\n\n# Aula\n\ntexto')
    # LLM devolve SEM frontmatter (caso de borda)
    enrich_file(f, FakeProvider(response="# Título\nconteúdo"))
    out = f.read_text()
    assert out.startswith("---")
    assert 'course: "X"' in out


# ─── enrich_directory ────────────────────────────────────────────────────


def test_enrich_directory_counts(tmp_path: Path):
    (tmp_path / "a1.md").write_text('---\ncourse: "X"\n---\n\n# Aula 1\ntexto')
    (tmp_path / "a2.md").write_text(
        'texto\n<!-- enriched-by: groq/x -->'
    )  # já enriquecido
    (tmp_path / "_MOC.md").write_text("# MOC\n")  # pulado (underscore)

    result = enrich_directory(tmp_path, FakeProvider(), delay=0, dry_run=False)

    # _MOC.md filtrado ANTES pela própria função; total_files conta só os elegíveis
    assert result.total_files == 2
    assert result.enriched == 1
    assert result.skipped == 1


def test_enrich_directory_dry_run_doesnt_write(tmp_path: Path):
    f = tmp_path / "aula.md"
    original = '---\ncourse: "X"\n---\n\n# Aula\ntexto'
    f.write_text(original)
    enrich_directory(tmp_path, FakeProvider(), delay=0, dry_run=True)
    assert f.read_text() == original


# ─── create_provider factory ─────────────────────────────────────────────


def test_create_provider_rejects_unknown():
    with pytest.raises(ValueError, match="não suportado"):
        create_provider("openai")


def test_create_provider_ollama_works_without_api_key():
    """Ollama local não precisa de API key."""
    p = create_provider("ollama")
    assert p.name().startswith("ollama/")


def test_create_provider_groq_without_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError
    with pytest.raises(ProviderAPIKeyMissingError):
        create_provider("groq")


def test_create_provider_claude_without_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from classroom_transcripter.core.exceptions import ProviderAPIKeyMissingError
    with pytest.raises(ProviderAPIKeyMissingError):
        create_provider("claude")


def test_create_provider_groq_strips_quotes_from_key():
    """Bug do v0.1: aspas do .env vazavam na Authorization header."""
    p = create_provider("groq", api_key='"my-key-with-quotes"')
    assert p.api_key == "my-key-with-quotes"
