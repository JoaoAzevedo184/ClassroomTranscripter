# 🎓 Classroom Transcripter

Ferramenta CLI que extrai transcrições de cursos **Udemy, DIO e Alura** e transforma em material de estudo com IA.

**Pipeline:** `download/transcribe` → `format` → `enrich`

> 🚧 **Em refatoração.** Esta versão (v0.2.0) é o esqueleto multi-source. Para a versão estável só-Udemy, veja `main` anteriormente (ex-`UdemyTranscripter`). Acompanhe o progresso em [`docs/refactor-plan.md`](docs/refactor-plan.md).

## Quick Start

```bash
git clone https://github.com/JoaoAzevedo184/ClassroomTranscripter.git
cd ClassroomTranscripter
pip install -e ".[dev]"
cp .env.example .env   # preencha o que você vai usar
```

## Comandos por plataforma

Cada plataforma tem o próprio CLI com flags específicas. O comando umbrella `classroom` aceita qualquer um deles como subcomando.

### Udemy

```bash
classroom-udemy --url "https://udemy.com/course/meu-curso/" --format obsidian --merge
# ou
classroom udemy --url "..." --format obsidian
```

### DIO (Whisper local em cima dos .mp4 que você baixou)

```bash
classroom-dio --video-dir ~/dio_videos/jornada-node --whisper-model small --format obsidian
```

### Alura

```bash
classroom-alura --url "https://cursos.alura.com.br/course/..." --format obsidian
```

### Enriquecer com IA (funciona em qualquer pasta gerada)

```bash
classroom-enrich ./transcripts/MeuCurso --provider groq
```

## Providers de IA

| Provider | Custo | Velocidade | Setup |
|---|---|---|---|
| **Groq** | Gratuito | Ultra-rápido | [console.groq.com](https://console.groq.com) |
| **Gemini** | Gratuito | Rápido | [aistudio.google.com](https://aistudio.google.com) |
| **Ollama** | Gratuito | Local | `ollama pull llama3.1` |
| **Claude** | Pago | Rápido | [console.anthropic.com](https://console.anthropic.com) |

## Arquitetura

Três camadas: `core/` (agnóstico) → `sources/{udemy,dio,alura}/` (plataforma) → `cli/` (interface).

Veja [`docs/arquitetura.md`](docs/arquitetura.md) pro racional completo.

```
src/classroom_transcripter/
├── core/              # models, formatters, enricher, vtt (compartilhado)
├── sources/           # udemy/, dio/, alura/ (implementam TranscriptSource)
└── cli/               # um CLI por plataforma + enrich
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [Arquitetura](docs/arquitetura.md) | Como o projeto é organizado |
| [Plano de Refatoração](docs/refactor-plan.md) | Checklist das 7 fases |
| [Configuração](docs/configuracao.md) | Cookies, API keys, `.env` |
| [Uso](docs/uso.md) | Pipeline completo |
| [Udemy](docs/sources/udemy.md) | Setup específico |
| [DIO](docs/sources/dio.md) | Whisper local, organização dos vídeos |
| [Alura](docs/sources/alura.md) | Login e limitações |

## Testes

```bash
pip install -e ".[dev]"
pytest -v
```

## Status da refatoração

## Status da refatoração — CONCLUÍDA ✅

- [x] Fase 1 — Esqueleto multi-source
- [x] Fase 2 — Migrar `core/` (144 testes)
- [x] Fase 3 — Extrair Udemy pra `sources/udemy/` (178 testes)
- [x] Fase 4 — Downloader genérico (198 testes)
- [x] Fase 5 — CLI modular (228 testes)
- [x] Fase 6 — Implementar DIO (273 testes)
- [x] Fase 7 — Esqueleto ativável da Alura (313 testes)

**Udemy e DIO estão 100% funcionais.** Alura precisa de 3 TODOs preenchidos após inspeção do DevTools — ver `docs/sources/alura.md`.

## Notas

- **Udemy/Alura:** só funciona com cursos **que você comprou**.
- **DIO:** você precisa baixar os .mp4 separadamente antes de rodar a transcrição.
- Respeite os termos de uso das plataformas (uso pessoal para estudo).
