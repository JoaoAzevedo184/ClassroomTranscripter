"""Orquestração do enriquecimento de transcrições com IA.

Lê arquivos .md gerados pelo ObsidianFormatter, envia pra uma LLM e reescreve
com foco educativo: estrutura visual, seções escaneáveis, blocos de código,
emojis nos headings, perguntas de revisão.

Plataforma-agnóstico: funciona em output de Udemy, DIO ou Alura.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from classroom_transcripter.core.enricher.base import LLMProvider


# ─── Resultado ──────────────────────────────────────────────────────────────


@dataclass
class EnrichResult:
    """Resultado do enriquecimento de um diretório."""

    total_files: int
    enriched: int
    skipped: int
    errors: int


# ─── Prompts (migrados do v0.1 sem alteração) ──────────────────────────────


SYSTEM_PROMPT = """\
Você é um assistente educacional especializado em transformar transcrições brutas \
de aulas em notas de estudo visualmente claras, didáticas e fáceis de escanear.

## Sua tarefa

Receba a transcrição (gerada a partir de áudio) de uma aula e reescreva como uma nota \
de estudo completa em Markdown, seguindo o formato visual descrito abaixo.

## Regras obrigatórias

1. **Mantenha o frontmatter YAML** (bloco `---`) EXATAMENTE como está, sem alterar
2. **Mantenha o callout de navegação** (`> [!tip] Navegação`) se existir
3. **Idioma**: responda no mesmo idioma da transcrição original
4. **Limpeza da fala**: remova vícios de linguagem (né, ahn, hum), repetições, frases \
incompletas e gaguejos. Transforme a linguagem oral em texto escrito claro e direto
5. **Não invente** informações que não estão na transcrição (zero alucinação)
6. **Não perca** conteúdo relevante — a nota deve ser exaustiva
7. Entregue APENAS o Markdown final. Sem introduções como "Aqui está a nota" ou "Claro"

## Formato visual obrigatório

### Emojis nos headings
Use emojis temáticos no início de cada seção principal (nível #):
- `# 📚 Visão Geral da Aula` — resumo do tema
- `# 🎯 Objetivos` — o que o aluno vai aprender
- `# 🧠 Conceitos` — conteúdo principal
- `# 🧾 Resumo da Aula` — pontos-chave
- `# 🔁 Perguntas para Revisão` — fixação
- `# ✍️ Anotações` — espaço do aluno (manter vazio)
- Use outros emojis quando apropriado (👨‍🏫, ⚙️, 🧩, 👥, etc.)

### Separadores visuais
Use `---` (horizontal rule) entre TODAS as seções principais para criar \
separação visual clara. Cada bloco `#` deve ser precedido por `---`.

### Estrutura das seções
- **Seções curtas e escaneáveis** — máximo 5-8 linhas por bloco
- **Um conceito por subseção** — se a aula fala sobre 5 conceitos, crie 5 subseções \
separadas com `##` ou `###`, cada uma com sua explicação breve
- **Bullet points curtos** — use listas com termos em **negrito** seguidos de explicação
- **Listas de checagem** — use ✅ e ❌ para indicar "foco do curso" vs "fora do escopo"

### Estrutura obrigatória do documento

```
[frontmatter YAML — não alterar]
[callout de navegação — se existir]
---
# 📚 Visão Geral da Aula
[1-2 parágrafos resumindo o tema central]
---
# 🎯 Objetivos / O que será aprendido
[lista de bullet points]
---
# 🧠 [Seções de conteúdo com emojis]
[conteúdo organizado por tópicos, com subsections ###]
[cada conceito em sua própria subseção]
[blocos de código quando houver comandos/código]
---
# 🧾 Resumo da Aula
[3-5 bullet points com as lições principais]
---
# 🔁 Perguntas para Revisão
[3-5 perguntas numeradas para fixação]
---
# ✍️ Anotações
> [!note] Espaço para suas anotações
>
> -
> -
> -
```

### Enriquecimento
- **Termos-chave** em negrito na primeira ocorrência
- **Blocos de código** (`bash`, `yaml`, `dockerfile`, etc.) quando a aula mencionar comandos
- **Callouts do Obsidian** quando agregar valor:
  - `> [!tip]` para dicas práticas
  - `> [!warning]` para pontos de atenção
  - `> [!info]` para conceitos fundamentais
  - `> [!example]` para exemplos e analogias
- Se a aula apresentar uma pessoa (instrutor), crie uma seção `# 👨‍🏫 Sobre o Instrutor`

### O que NÃO fazer
- Não use parágrafos longos — quebre em blocos curtos
- Não use a seção `## Transcrição` — reorganize todo o conteúdo por tópicos
- Não altere o frontmatter YAML
- Não adicione código incorreto ou inventado
- Não use o formato TL;DR — use `# 📚 Visão Geral da Aula` no lugar
"""


ENRICH_USER_TEMPLATE = """\
## Contexto do curso
- **Curso**: {course_title}
- **Seção**: {section_title}
- **Aula**: {lecture_title}

## Transcrição original (nota Obsidian)

{content}

---

Reescreva esta nota seguindo o formato visual com emojis nos headings, \
separadores entre seções, blocos curtos e escaneáveis. \
Reorganize TODO o conteúdo por tópicos — não mantenha a seção "## Transcrição"."""


# ─── Lógica de Enriquecimento ──────────────────────────────────────────────


_ENRICHED_MARKER = "<!-- enriched-by:"


def is_enriched(content: str) -> bool:
    """Checa se o arquivo já foi enriquecido (tem marker no final)."""
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
    """Extrai campos básicos do frontmatter pra passar de contexto no prompt."""
    meta: dict[str, str] = {}
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
    """Enriquece um único arquivo .md.

    Args:
        file_path: arquivo .md a enriquecer.
        provider: LLMProvider (Ollama/Claude/Groq/Gemini).
        dry_run: se True, apenas mostra o que faria sem escrever.

    Returns:
        True se enriqueceu, False se pulou (já enriquecido / arquivo _index etc).
    """
    content = file_path.read_text(encoding="utf-8")

    if is_enriched(content):
        return False

    # Arquivos começando com _ (ex: _MOC.md, _index.md) são metadados, não aulas
    if file_path.name.startswith("_"):
        return False

    frontmatter, body = _extract_frontmatter(content)
    meta = _extract_metadata_from_frontmatter(frontmatter)

    title_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    lecture_title = title_match.group(1) if title_match else file_path.stem

    user_prompt = ENRICH_USER_TEMPLATE.format(
        course_title=meta.get("course", "Desconhecido"),
        section_title=meta.get("section", "Desconhecida"),
        lecture_title=lecture_title,
        content=content,
    )

    if dry_run:
        print(f"   [DRY RUN] Enviaria {file_path.name} para {provider.name()}")
        return True

    enriched = provider.complete(SYSTEM_PROMPT, user_prompt)

    if frontmatter and not enriched.strip().startswith("---"):
        enriched = frontmatter + "\n" + enriched

    marker = f"{_ENRICHED_MARKER} {provider.name()} -->\n"
    enriched = enriched.rstrip() + "\n\n" + marker

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
        directory: diretório raiz do curso (saída do download).
        provider: LLMProvider.
        delay: delay entre chamadas (segundos).
        dry_run: se True, não salva alterações.

    Returns:
        EnrichResult com estatísticas.
    """
    md_files = sorted(directory.rglob("*.md"))
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
