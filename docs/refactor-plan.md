# Plano de Refatoração: Multi-Source

> **Branch:** `refactor/multi-source`
> **Objetivo:** sair de um projeto acoplado à Udemy (`udemy_transcripter/`) pra um projeto multi-plataforma com Udemy, DIO e Alura (`classroom_transcripter/`).

## Princípios

1. **Cada fase é um PR/commit que mantém `pytest -v` verde.**
2. **Renomeação e movimentação antes de reescrita.** Só reescreve código depois que a nova estrutura tá estável.
3. **Interface primeiro, implementação depois.** A ABC `TranscriptSource` (`sources/base.py`) já existe; os sources concretos preenchem ela gradualmente.

---

## ✅ Fase 1 — Esqueleto (esta entrega)

Estrutura física nova, sem lógica migrada ainda.

- [x] `pyproject.toml` renomeado pra `classroom-transcripter`
- [x] src-layout (`src/classroom_transcripter/`)
- [x] Entry points: `classroom`, `classroom-udemy`, `classroom-dio`, `classroom-alura`, `classroom-enrich`
- [x] `core/models.py` com dataclasses implementadas
- [x] `core/exceptions.py` com hierarquia implementada
- [x] `sources/base.py` — ABC `TranscriptSource` documentada
- [x] Placeholders com docstrings de migração pra todas as fases seguintes
- [x] `docs/arquitetura.md` + este plano
- [x] `tests/test_structure.py` — valida que a estrutura está correta

**Critério de done:** `pip install -e ".[dev]"` + `pytest tests/test_structure.py` verde.

---

## Fase 2 — Migrar `core/`

Move código agnóstico-de-plataforma do repo atual pro `core/`.

- [ ] `core/config.py` ← `udemy_transcripter/config.py`
  - [ ] Adicionar variáveis novas: `DIO_VIDEO_DIR`, `WHISPER_MODEL`, `ALURA_EMAIL`, `ALURA_PASSWORD`
- [ ] `core/utils.py` ← parte agnóstica de `udemy_transcripter/utils.py`
  - [ ] Funções específicas da Udemy continuam em `sources/udemy/` (Fase 3)
- [ ] `core/vtt.py` ← `udemy_transcripter/vtt.py`
  - [ ] Adaptar retorno pra `list[TranscriptCue]` de `core.models`
- [ ] `core/formatters/txt.py` ← parte TxtFormatter de `formatters.py`
- [ ] `core/formatters/obsidian.py` ← parte ObsidianFormatter de `formatters.py`
  - [ ] Adicionar campo `platform` no frontmatter
- [ ] `core/enricher/pipeline.py` ← orquestração de `enricher.py`
- [ ] `core/enricher/providers/{groq,gemini,ollama,claude}.py` ← um por provider
- [ ] Migrar testes pra `tests/core/`:
  - [ ] `tests/core/test_config.py`
  - [ ] `tests/core/test_utils.py`
  - [ ] `tests/core/test_vtt.py`
  - [ ] `tests/core/test_formatters.py`
  - [ ] `tests/core/test_enricher.py`

**Critério de done:** todos os 69 testes originais passando nos novos paths.

---

## Fase 3 — Extrair Udemy pra `sources/udemy/`

- [ ] `sources/udemy/client.py` ← `udemy_transcripter/client.py` (imports atualizados)
- [ ] `sources/udemy/parser.py` ← extraído de `downloader.py` (parsing da API)
- [ ] `sources/udemy/source.py` — implementação de `UdemySource(TranscriptSource)`
  - [ ] `authenticate()` valida cookie via `/users/me`
  - [ ] `fetch_course(url_or_slug)` devolve `Course`
  - [ ] `fetch_transcript(lecture)` devolve `Transcript` parseado via `core/vtt.py`
  - [ ] `list_available_languages(lecture)` pra `--list-langs`
- [ ] Migrar `tests/sources/udemy/test_client.py`

**Critério de done:** `UdemySource` funcional com mocks; testes do cliente passando.

---

## Fase 4 — Downloader genérico no `core/`

Hoje o `downloader.py` mistura fluxo + parsing da Udemy. Separar:

- [ ] Criar `core/downloader.py`:
  ```python
  def download_course(source: TranscriptSource, course: Course,
                      formatter: BaseFormatter, output_dir: Path,
                      *, include_timestamps=False, merge=False) -> DownloadResult:
      ...
  ```
- [ ] Remover `udemy_transcripter/downloader.py` (virou genérico + parser.py)
- [ ] Testes: `tests/core/test_downloader.py` com mock de `TranscriptSource`

**Critério de done:** testes de integração Udemy passam usando `UdemySource` + downloader genérico.

---

## Fase 5 — CLI modular

- [ ] `cli/udemy_cli.py` ← migrar flags Udemy de `cli.py` atual
- [ ] `cli/enrich_cli.py` ← migrar flags `--enrich` de `cli.py` atual
- [ ] `cli/main.py` dispatcher umbrella (já implementado na Fase 1)
- [ ] Remover `udemy_transcripter/cli.py` antigo
- [ ] README atualizado com novos comandos

**Critério de done:** `classroom-udemy --url ... --format obsidian` funciona end-to-end igual ao `python -m udemy_transcripter` antigo.

---

## Fase 6 — Implementar DIO

- [ ] `sources/dio/whisper_engine.py` ← copiar do repo `whisper-transcriber`
  - [ ] Adaptar retorno pra `Transcript` de `core.models`
  - [ ] Lazy import do `whisper` (pesado)
- [ ] `sources/dio/video_finder.py` — descoberta de Course via convenção de pastas
- [ ] `sources/dio/source.py` — `DioSource(TranscriptSource)`
- [ ] `cli/dio_cli.py`
- [ ] Testes com fixtures de pastas simuladas (`tmp_path`)
- [ ] `docs/sources/dio.md` — como baixar os .mp4, organizar pastas, instalar Whisper

**Critério de done:** `classroom-dio --video-dir ./fixture-bootcamp` gera .md Obsidian corretos pra um mini-bootcamp de teste.

---

## Fase 7 — Implementar Alura

- [ ] Inspecionar DevTools → Network da Alura logado (mapear endpoints reais)
- [ ] `sources/alura/client.py` — login + sessão
- [ ] `sources/alura/parser.py` — HTML/JSON → Course/Transcript
- [ ] `sources/alura/source.py` — `AluraSource(TranscriptSource)`
- [ ] `cli/alura_cli.py`
- [ ] Testes com HTML/JSON fixtures (offline)
- [ ] `docs/sources/alura.md` — credenciais, limitações, FAQ

**Critério de done:** `classroom-alura --url ...` funciona num curso real (teste manual).

---

## Pós-refatoração

- [ ] Atualizar README principal (nova estrutura, 3 plataformas)
- [ ] Tag v0.2.0
- [ ] Issue "roadmap Coursera/Rocketseat?" (opcional)
