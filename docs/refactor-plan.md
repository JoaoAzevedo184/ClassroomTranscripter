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

## ✅ Fase 2 — Migrar `core/` (CONCLUÍDA)

- [x] `core/models.py` — modelos purista: `Course`, `Module`, `Lecture`, `Caption`, `Transcript`, `TranscriptCue`, `DownloadResult` (com `platform` e `skipped`)
- [x] `core/exceptions.py` — hierarquia `TranscripterError` + alias `NoCaptionsError` retrocompatível
- [x] `core/config.py` — Udemy (mantido) + DIO + Alura + Whisper + aliases v0.1
- [x] `core/platforms.py` — `BasePlatform` + `UdemyPlatform`, `DioPlatform`, `AluraPlatform`
- [x] `core/utils.py` — `extract_slug` usando `detect_platform` novo
- [x] `core/vtt.py` — migrado + nova `vtt_to_transcript()` devolvendo `Transcript`
- [x] `core/formatters/{base,txt,obsidian}.py` — split em 3 arquivos, `platform` dinâmico no frontmatter
- [x] `core/enricher/base.py` — `LLMProvider` + `_post_with_retry` compartilhado
- [x] `core/enricher/pipeline.py` — prompts + `enrich_file` + `enrich_directory`
- [x] `core/enricher/providers/{ollama,claude,groq,gemini}.py` — 4 providers separados
- [x] `core/enricher/__init__.py` — factory `create_provider` com lazy imports
- [x] Testes migrados em `tests/core/`: config, models, platforms, utils, vtt, formatters, enricher
- [x] **144 testes passando** (53 da Fase 1 + 91 novos da Fase 2)

**Status:** 🟢 Concluída. Pronto para Fase 3.

---

## ✅ Fase 3 — Extrair Udemy pra `sources/udemy/` (CONCLUÍDA)

- [x] `sources/udemy/client.py` — migrado do v0.1, usa `core.config.UDEMY_*` e `core.exceptions`
  - `get_curriculum()` agora devolve `list[Module]` (era `list[Section]`)
- [x] `sources/udemy/parser.py` — `build_course()` monta `Course` a partir das partes do client
- [x] `sources/udemy/source.py` — `UdemySource(TranscriptSource)` completo:
  - `authenticate()` valida cookie via `/users/me`
  - `fetch_course(url_or_slug)` devolve `Course`
  - `fetch_transcript(lecture)` escolhe caption + baixa VTT + parseia → `Transcript`
  - `list_available_languages(lecture)` pra `--list-langs`
  - `_client` lazy (facilita testes)
- [x] `sources/udemy/__init__.py` — re-exports
- [x] Testes: `tests/sources/udemy/test_client.py` (13), `test_source.py` (18), `test_parser.py` (3)
- [x] **178 testes verdes** (144 da Fase 2 + 34 novos da Fase 3)

**Status:** 🟢 Concluída. Pronto para Fase 4 (downloader genérico usando `TranscriptSource`).

---

## ✅ Fase 4 — Downloader genérico (CONCLUÍDA)

- [x] `core/downloader.py` — orquestra qualquer `TranscriptSource`:
  - `download_course(source, course, ...)` — orquestração pura
  - `download_by_identifier(source, identifier, ...)` — conveniência (faz `fetch_course` + download)
  - `list_available_captions(source, course)` — lista idiomas disponíveis
- [x] Features preservadas do v0.1:
  - `--resume` (pula aulas cujo arquivo já existe)
  - `--merge` (gera `_CURSO_COMPLETO.txt|.md`)
  - Navegação prev/next pra wikilinks do Obsidian
  - `_metadata.json` (+ campo `platform` na v0.2)
- [x] Suporte DIO nativo: heurística `_lecture_is_available` reconhece tanto `captions` (Udemy/Alura) quanto `metadata["file"]` (DIO)
- [x] Timestamps multi-fonte: `_transcript_to_text` sabe lidar com `cues` (Whisper/VTT) e `plain_text` (scraping)
- [x] Testes `tests/core/test_downloader.py` (20) com `FakeSource` — valida integração completa sem HTTP
- [x] **198 testes verdes** (178 da Fase 3 + 20 novos)

**Status:** 🟢 Concluída. Todo o pipeline agnóstico tá pronto — Fase 5 já pode consumir `download_course(source, ...)` nos CLIs.

---

## ✅ Fase 5 — CLI modular (CONCLUÍDA)

- [x] `cli/udemy_cli.py` — CLI completo da Udemy consumindo `UdemySource` + `download_course`
  - Todas as flags do v0.1: `--url`, `--cookie`, `--format`, `--lang`, `--merge`, `--resume`, `--list-langs`, `--timestamps`, `--setup`, `--debug`
  - ObsidianFormatter recebe `platform="udemy"` automaticamente
  - `--setup` delega pro `setup_cli.setup_env`
- [x] `cli/enrich_cli.py` — CLI agnóstico de plataforma
  - Captura `TranscripterError` (inclui `ProviderAPIKeyMissingError`) com mensagem amigável
  - Forwards corretos: `--model`, `--ollama-url`, `--timeout`, `--delay`, `--dry-run`
- [x] `cli/setup_cli.py` — NOVO na Fase 5, migra o `setup.py` do v0.1
- [x] `cli/main.py` — dispatcher umbrella expandido com `setup`
- [x] Entry points registrados: `classroom`, `classroom-udemy`, `classroom-dio`, `classroom-alura`, `classroom-enrich`, `classroom-setup`
- [x] Testes novos (30): `tests/cli/test_udemy_cli.py`, `test_enrich_cli.py`, `test_main_dispatcher.py`
- [x] **228 testes verdes** (198 da Fase 4 + 30 novos)
- [x] Smoke manual: `classroom --help`, `classroom-udemy --help`, `classroom-enrich --help` funcionam após `pip install -e .`

**Status:** 🟢 Concluída. O pacote `udemy_transcripter/` v0.1 pode ser apagado do repo agora — `classroom-udemy` faz tudo que ele fazia.

---

## ✅ Fase 6 — Implementar DIO (CONCLUÍDA)

- [x] `sources/dio/video_finder.py` — estrutura profunda obrigatória (uma subpasta por módulo)
  - Natural sort (01, 02, ..., 10 na ordem certa)
  - Prettify de nomes (`01-introducao` → `Introducao`)
  - Aceita .mp4, .mkv, .webm, .mov, .m4a, .mp3, .wav
  - Estrutura plana é ERRO (CourseNotFoundError com instruções)
- [x] `sources/dio/whisper_engine.py` — wrapper do Whisper, SEM cache em disco
  - Modelo carregado lazy + cacheado em memória via `lru_cache` (pro mesmo run)
  - Converte segmentos do Whisper em `TranscriptCue[]`
  - Estratégia de retomada: `--resume` do downloader genérico (evita retranscrever aulas que já viraram .md)
- [x] `sources/dio/source.py` — `DioSource(TranscriptSource)`, `authenticate` é no-op
- [x] `cli/dio_cli.py` — `classroom-dio --video-dir ... --whisper-model small --resume`
- [x] Testes novos: `tests/sources/dio/test_video_finder.py` (17), `test_whisper_engine.py` (10), `test_source.py` (7), `tests/cli/test_dio_cli.py` (11)
- [x] Teste de integração confirma: `DioSource` + `download_course` genérico + `--resume` funcionam juntos
- [x] **273 testes verdes** (228 da Fase 5 + 45 novos)

**Status:** 🟢 Concluída. A arquitetura `TranscriptSource` passou no "real-world test" — DIO (Whisper local, sem API, sem auth) funciona com o mesmo downloader genérico que a Udemy (API + VTT + Cloudflare).

---

## ✅ Fase 7 — Implementar Alura (CONCLUÍDA como esqueleto ativável)

- [x] `sources/alura/client.py` — `AluraClient` com httpx session + 3 métodos marcados `NotImplementedError("TODO Fase 7.N")`, docstrings detalhadas com exemplo de implementação
- [x] `sources/alura/parser.py` — IMPLEMENTADO COMPLETO. `parse_course()` + `parse_transcript()` suportando 3 formatos (segments, plain text, VTT)
- [x] `sources/alura/source.py` — `AluraSource(TranscriptSource)` completo, só delega pro client+parser (cliente lazy)
- [x] `cli/alura_cli.py` — CLI completa com `--url`, `--email`, `--password`, `--ask-password`, `.env`, `--merge`, `--resume`. Mensagem amigável quando TODOs não preenchidos.
- [x] `docs/sources/alura.md` — guia passo-a-passo detalhado de como inspecionar DevTools e preencher os 3 TODOs
- [x] Testes: `test_parser.py` (14), `test_source.py` (11), `test_client.py` (8), `test_alura_cli.py` (10) = 43 testes
- [x] **313 testes verdes** (273 da Fase 6 + 40 novos)

**Status:** 🟡 Esqueleto ativável. Arquitetura 100% pronta; 3 funções HTTP reais pendentes (aguardam sua inspeção de DevTools).

**Pra ativar:**
1. Abra `docs/sources/alura.md`
2. Faça a inspeção (1-2h)
3. Preencha os 3 TODOs em `sources/alura/client.py`
4. Rode `classroom-alura --url "..." --debug`

Quando ativar, não precisa mudar nem arquitetura, nem CLI, nem testes — só as 3 funções.

---

## Pós-refatoração

- [ ] Atualizar README principal (nova estrutura, 3 plataformas)
- [ ] Tag v0.2.0
- [ ] Issue "roadmap Coursera/Rocketseat?" (opcional)
