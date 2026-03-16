"""Enriquecimento de transcrições com IA.

Lê arquivos .md gerados pelo Obsidian formatter, envia para uma LLM
e reescreve com foco educativo: código, estrutura, exemplos.

Providers suportados:
- Ollama (local, gratuito)
- Claude API (Anthropic)
"""

from __future__ import annotations

import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

# ─── Resultado ──────────────────────────────────────────────────────────────


@dataclass
class EnrichResult:
    """Resultado do enriquecimento."""

    total_files: int
    enriched: int
    skipped: int
    errors: int


# ─── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
Você é um assistente educacional especializado em criar material de estudo \
de alta qualidade a partir de transcrições de aulas.

## Sua tarefa

Receba a transcrição de uma aula e reescreva como uma nota de estudo \
completa e educativa em Markdown, mantendo o frontmatter YAML original intacto.

## Regras obrigatórias

1. **Mantenha o frontmatter YAML** (bloco `---`) EXATAMENTE como está, sem alterar
2. **Mantenha a seção "## Anotações"** no final (vazia para o aluno preencher)
3. **Mantenha o callout de navegação** (`> [!tip] Navegação`) se existir
4. **Idioma**: responda no mesmo idioma da transcrição original
5. **Extensão**: a nota enriquecida deve ser mais completa que a transcrição original

## O que você deve fazer

### Estrutura educativa
- Reorganize o conteúdo com **headings claros** (##, ###)
- Separe em seções lógicas (conceito → explicação → exemplo → resumo)
- Adicione **bullet points** para listas de conceitos
- Inclua um **TL;DR** no topo com os pontos principais da aula

### Código e exemplos práticos
- Adicione **blocos de código** que ilustrem os conceitos da aula
- Use a linguagem/tecnologia correta do contexto do curso
- Inclua comentários explicativos no código
- Se a aula menciona comandos, liste-os em blocos ```bash```
- Adicione exemplos de **input/output** quando relevante

### Enriquecimento pedagógico
- Destaque **termos-chave** em negrito na primeira ocorrência
- Adicione callouts do Obsidian para dicas importantes:
  - `> [!tip]` para dicas práticas
  - `> [!warning]` para armadilhas comuns
  - `> [!example]` para exemplos extras
  - `> [!question]` para perguntas de revisão
- Ao final, antes de "## Anotações", inclua:
  - `## Pontos-chave` com 3-5 bullet points resumindo a aula
  - `## Perguntas de revisão` com 2-3 perguntas para fixação

### O que NÃO fazer
- Não invente informações que contradizem a transcrição
- Não remova conteúdo relevante da transcrição original
- Não altere o frontmatter YAML
- Não adicione código incorreto ou desatualizado
- Não mude o idioma da nota
"""

ENRICH_USER_TEMPLATE = """\
## Contexto do curso
- **Curso**: {course_title}
- **Seção**: {section_title}
- **Aula**: {lecture_title}

## Transcrição original (nota Obsidian)

{content}

---

Reescreva esta nota mantendo o frontmatter YAML intacto, \
reorganizando com foco educativo e adicionando blocos de código \
e exemplos práticos condizentes com o tema da aula."""


# ─── Providers ──────────────────────────────────────────────────────────────


class LLMProvider(ABC):
    """Interface para provedores de LLM."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Envia prompt e retorna resposta da LLM."""

    @abstractmethod
    def name(self) -> str:
        """Nome do provider para logs."""


class OllamaProvider(LLMProvider):
    """Provider local via Ollama API."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def name(self) -> str:
        return f"ollama/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 16384,
                },
            },
            timeout=300,
        )

        if not resp.ok:
            try:
                error_msg = resp.json().get("error", resp.text[:500])
            except Exception:
                error_msg = resp.text[:500]
            raise RuntimeError(f"Ollama {resp.status_code}: {error_msg}")

        return resp.json()["message"]["content"]


class ClaudeProvider(LLMProvider):
    """Provider via Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        raw_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        # Limpa aspas que podem vir do .env
        self.api_key = raw_key.strip().strip('"').strip("'") if raw_key else None
        self.model = model
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não encontrada. "
                "Defina via --api-key ou no .env."
            )

    def name(self) -> str:
        return f"claude/{self.model}"

    def complete(self, system: str, user: str) -> str:
        import requests

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 8192,
                "system": system,
                "messages": [
                    {"role": "user", "content": user},
                ],
            },
            timeout=300,
        )

        # Mostra erro real da API em vez de "400 Bad Request"
        if not resp.ok:
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", resp.text)
                error_type = error_data.get("error", {}).get("type", "unknown")
            except Exception:
                error_msg = resp.text[:500]
                error_type = "unknown"

            raise RuntimeError(
                f"Claude API {resp.status_code} ({error_type}): {error_msg}"
            )

        data = resp.json()
        return data["content"][0]["text"]


# ─── Registry de Providers ──────────────────────────────────────────────────


def create_provider(
    provider_name: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """Cria um provider de LLM pelo nome.

    Args:
        provider_name: "ollama" ou "claude"
        model: Modelo a usar (padrão depende do provider)
        api_key: API key (necessário para claude)
        base_url: URL base (para ollama customizado)
    """
    if provider_name == "ollama":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if base_url:
            kwargs["base_url"] = base_url
        return OllamaProvider(**kwargs)

    elif provider_name == "claude":
        kwargs = {}
        if model:
            kwargs["model"] = model
        if api_key:
            kwargs["api_key"] = api_key
        return ClaudeProvider(**kwargs)

    else:
        raise ValueError(
            f"Provider '{provider_name}' não suportado. "
            "Use 'ollama' ou 'claude'."
        )


# ─── Lógica de Enriquecimento ──────────────────────────────────────────────


_ENRICHED_MARKER = "<!-- enriched-by:"


def is_enriched(content: str) -> bool:
    """Verifica se o arquivo já foi enriquecido."""
    return _ENRICHED_MARKER in content


def _extract_frontmatter(content: str) -> tuple[str, str]:
    """Separa frontmatter YAML do corpo.

    Returns:
        (frontmatter_com_delimitadores, corpo)
    """
    if not content.startswith("---"):
        return "", content

    end = content.find("---", 3)
    if end == -1:
        return "", content

    end += 3
    return content[:end], content[end:]


def _extract_metadata_from_frontmatter(frontmatter: str) -> dict[str, str]:
    """Extrai campos básicos do frontmatter para contexto."""
    meta = {}
    for line in frontmatter.splitlines():
        for key in ("course", "section"):
            if line.strip().startswith(f"{key}:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                meta[key] = val
    return meta


def enrich_file(
    file_path: Path,
    provider: LLMProvider,
    dry_run: bool = False,
) -> bool:
    """Enriquece um único arquivo .md com IA.

    Args:
        file_path: Caminho do arquivo.
        provider: Provider de LLM.
        dry_run: Se True, não salva (apenas mostra o que faria).

    Returns:
        True se enriqueceu, False se pulou.
    """
    content = file_path.read_text(encoding="utf-8")

    # Pula se já enriquecido
    if is_enriched(content):
        return False

    # Pula arquivos especiais
    if file_path.name.startswith("_"):
        return False

    # Extrai metadados para contexto
    frontmatter, body = _extract_frontmatter(content)
    meta = _extract_metadata_from_frontmatter(frontmatter)

    # Extrai título da aula do heading
    title_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    lecture_title = title_match.group(1) if title_match else file_path.stem

    # Monta o prompt
    user_prompt = ENRICH_USER_TEMPLATE.format(
        course_title=meta.get("course", "Desconhecido"),
        section_title=meta.get("section", "Desconhecida"),
        lecture_title=lecture_title,
        content=content,
    )

    if dry_run:
        print(f"   [DRY RUN] Enviaria {file_path.name} para {provider.name()}")
        return True

    # Chama a LLM
    enriched = provider.complete(SYSTEM_PROMPT, user_prompt)

    # Garante que o frontmatter original foi preservado
    # (a LLM pode ter alterado — reconstrói se necessário)
    if frontmatter and not enriched.strip().startswith("---"):
        enriched = frontmatter + "\n" + enriched

    # Adiciona marcador de enriquecimento
    marker = f"{_ENRICHED_MARKER} {provider.name()} -->\n"
    enriched = enriched.rstrip() + "\n\n" + marker

    # Salva
    file_path.write_text(enriched, encoding="utf-8")
    return True


def enrich_directory(
    directory: Path,
    provider: LLMProvider,
    delay: float = 1.0,
    dry_run: bool = False,
) -> EnrichResult:
    """Enriquece todos os .md de um diretório de curso.

    Args:
        directory: Diretório raiz do curso (saída do download).
        provider: Provider de LLM.
        delay: Delay entre chamadas (segundos).
        dry_run: Se True, não salva alterações.

    Returns:
        EnrichResult com estatísticas.
    """
    md_files = sorted(directory.rglob("*.md"))

    # Filtra arquivos especiais (_MOC.md, _index.md, _CURSO_COMPLETO.md)
    md_files = [f for f in md_files if not f.name.startswith("_")]

    total = len(md_files)
    enriched = 0
    skipped = 0
    errors = 0

    print(f"\n🤖 Enriquecendo {total} notas com {provider.name()}")
    if dry_run:
        print("   [DRY RUN] Nenhum arquivo será alterado\n")

    for i, file_path in enumerate(md_files, 1):
        relative = file_path.relative_to(directory)
        print(f"   [{i}/{total}] {relative}", end="")

        try:
            if is_enriched(file_path.read_text(encoding="utf-8")):
                print(" (já enriquecido, pulando)")
                skipped += 1
                continue

            result = enrich_file(file_path, provider, dry_run=dry_run)
            if result:
                enriched += 1
                print(" ✓")
            else:
                skipped += 1
                print(" (pulado)")

            if not dry_run and i < total:
                time.sleep(delay)

        except Exception as e:
            errors += 1
            print(f" ✗ {e}")

    print("\n✓ Enriquecimento concluído!")
    print(f"  Enriquecidos: {enriched}")
    if skipped:
        print(f"  Pulados: {skipped}")
    if errors:
        print(f"  Erros: {errors}")

    return EnrichResult(
        total_files=total,
        enriched=enriched,
        skipped=skipped,
        errors=errors,
    )