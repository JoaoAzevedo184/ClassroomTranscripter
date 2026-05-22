# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [0.2.0] — 2026-05-21

Reescrita multi-plataforma. O projeto deixa de ser `udemy_transcripter` e vira
`classroom_transcripter`, com suporte a Udemy, DIO e Alura compartilhando o mesmo
pipeline de download → format → enrich.

### Adicionado

- **Arquitetura em 3 camadas:** `core/` (agnóstico) → `sources/` (plataforma) →
  `cli/` (interface). Veja [`docs/arquitetura.md`](arquitetura.md)
- **ABC `TranscriptSource`** (`sources/base.py`) — contrato que cada plataforma
  implementa. Todo o resto do pipeline (downloader, formatters, enricher) é
  100% agnóstico de plataforma
- **Modelos novos no core:**
  - `Course` (agrega o curso inteiro com slug, idioma, módulos)
  - `Transcript` + `TranscriptCue` (encapsula texto + timestamps)
  - `Module` (renomeação universal de `Section`)
  - `DownloadResult.platform` e `DownloadResult.skipped` para suportar `--resume`
- **DIO via Whisper local** (`classroom-dio`) — transcreve `.mp4` baixados
  manualmente. Suporta tiny/base/small/medium/large. Cache em memória via
  `lru_cache` (sem cache em disco — `--resume` cobre retomada)
- **Alura como esqueleto ativável** (`classroom-alura`) — arquitetura 100%
  pronta, parser implementado pra 3 formatos (segments, plain text, VTT).
  3 TODOs marcados em `sources/alura/client.py` aguardam inspeção do DevTools.
  Guia passo-a-passo em [`docs/sources/alura.md`](sources/alura.md)
- **CLI umbrella `classroom <subcomando>`** + entry points específicos
  (`classroom-udemy`, `classroom-dio`, `classroom-alura`, `classroom-enrich`,
  `classroom-setup`)
- **Downloader genérico** (`core/downloader.py`) com `--resume`, `--merge`,
  navegação prev/next e `_metadata.json` — todos features funcionam pras 3
  plataformas
- **Formatter Obsidian dinâmico** — frontmatter e tags refletem a plataforma de
  origem (`platform: udemy` vs `platform: dio` vs `platform: alura`)
- **313 testes** organizados em `tests/core/`, `tests/sources/{udemy,dio,alura}/`
  e `tests/cli/`. Testes de integração usam `FakeSource` (sem HTTP) e
  `_load_model` mockado (sem GPU)
- Hierarquia de exceções enraizada em `TranscripterError`. Alias retrocompatível
  `NoCaptionsError → TranscriptNotAvailableError` (será removido em v0.3)

### Alterado

- **Pacote renomeado:** `udemy_transcripter` → `classroom_transcripter`
- **Vocabulário universalizado:** `Section` → `Module` (afeta dataclasses,
  parâmetros de formatters e wikilinks gerados pelo Obsidian)
- **Providers de IA** continuam usando HTTP direto via `requests` (sem SDKs
  proprietários). Os extras `[groq]`, `[gemini]`, `[claude]`, `[ollama]`,
  `[ai-all]` foram removidos do `pyproject.toml` — eram dead-weight
- `requests` promovido de dep "escondida" para dependência base explícita
  (provedores de IA + download de VTT da Udemy dependem dele)
- `httpx` adicionado como dep base (cliente HTTP da Alura — `requests` não
  persiste cookies tão bem entre redirects)
- `beautifulsoup4` adicionado como dep base (scraping opcional do HTML da Alura)

### Removido

- Pacote `udemy_transcripter/` (substituído por `classroom_transcripter`)
- Testes velhos em `tests/test_*.py` (substituídos pelos novos em `tests/core/`,
  `tests/sources/` e `tests/cli/`)
- `Requirements.txt` (estava obsoleto; use `pip install -e ".[dev]"` ou
  `pip install 'classroom-transcripter[dio,dev]'`)
- Extras `[groq]`, `[gemini]`, `[claude]`, `[ollama]`, `[ai-all]`, `[all]` —
  inúteis porque o código usa HTTP direto

### Migração da v0.1

```python
# v0.1
from udemy_transcripter import UdemyClient, download_transcripts
client = UdemyClient(cookie)
download_transcripts(client, slug="meu-curso")

# v0.2
from classroom_transcripter.sources.udemy import UdemySource
from classroom_transcripter.core.downloader import download_by_identifier
source = UdemySource(cookie=cookie)
download_by_identifier(source, "meu-curso")
```

```bash
# v0.1
python -m udemy_transcripter --url "..." --format obsidian
python -m udemy_transcripter --enrich ./udemy_transcripts/X --provider groq

# v0.2
classroom-udemy --url "..." --format obsidian
classroom-enrich ./udemy_transcripts/X --provider groq
```

---

## [0.1.1] — 2026-04-20

> Era versão `1.1.0` na nomenclatura antiga. Renumerada para 0.1.x porque o
> projeto ainda não tinha API estável em 1.x.

### Adicionado

- `platforms.py` com abstração `BasePlatform` (preparação pra multi-source)
- `--resume` / `-r` para retomar sessões interrompidas
- `.env.example` com documentação inline
- `LANG_PRIORITY` configurável via `.env`
- `get_lang_priority()` em `config.py`
- `detect_platform(url)` e `get_platform(name)`
- Entrypoint `classroom-transcripter` no `pyproject.toml`

### Corrigido

- `Requirements.txt` — removida dependência `google-generativeai` não usada
- `formatters.py` — `import re` movido para o topo do arquivo
- `downloader.py` — relatório final separa aulas puladas das baixadas

### Alterado

- `LLMProvider` ganhou `_post_with_retry()` compartilhado entre Groq/Gemini
- `utils.extract_slug()` delega pra `UdemyPlatform.extract_slug()`

---

## [0.1.0] — 2026-04-19

> Era versão `1.0.0` na nomenclatura antiga. Lançamento inicial do projeto.

### Adicionado

- Download de transcrições da Udemy via API interna
- Bypass de Cloudflare usando `curl_cffi` com fingerprint Chrome
- Formatadores `txt` e `obsidian`
- Enriquecimento com IA via Ollama, Groq, Gemini e Claude
- `--merge`, `--timestamps`, `--list-langs`, `--setup`, `--dry-run`
- 69 testes unitários