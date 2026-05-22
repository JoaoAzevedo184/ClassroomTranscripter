# 🎓 Classroom Transcripter

Ferramenta CLI multi-plataforma que extrai transcrições de cursos **Udemy, DIO
e Alura** e transforma em material de estudo com IA.

**Pipeline:** `download/transcribe` → `format` → `enrich`

Pacote único, arquitetura em 3 camadas (`core` → `sources` → `cli`), 313 testes
passando. Veja [`docs/arquitetura.md`](docs/arquitetura.md) pro racional
completo.

## Status das plataformas

| Plataforma | Status | Como funciona |
|------------|:---:|---|
| **Udemy** | ✅ Pronto | API interna + bypass Cloudflare via `curl_cffi` |
| **DIO** | ✅ Pronto | Whisper local sobre `.mp4` baixados manualmente |
| **Alura** | 🟡 Esqueleto | Arquitetura pronta; 3 funções HTTP aguardam inspeção do DevTools — veja [`docs/sources/alura.md`](docs/sources/alura.md) |

## Quick Start

```bash
git clone https://github.com/JoaoAzevedo184/ClassroomTranscripter.git
cd ClassroomTranscripter

# Criar ambiente Virtual
python3 -m venv venv

# Ativar o Ambiente Virtual
source venv/bin/activate

# Instalação base (Udemy + Alura + 4 providers de IA)
pip install -e .

# Pra usar DIO (Whisper local), adicione o extra [dio]
pip install -e '.[dio]'

# Pra desenvolver
pip install -e '.[dev]'

# Configure as credenciais que você vai usar
cp .env.example .env
# (edite o .env com seus cookies/API keys)
```

> 💡 Os 4 providers de IA (Ollama, Groq, Gemini, Claude) funcionam via HTTP
> direto — não precisam de SDKs proprietários. A instalação base já inclui
> tudo que precisa.

## Comandos por plataforma

Cada plataforma tem o próprio CLI com flags específicas. O comando umbrella
`classroom` aceita qualquer um deles como subcomando.

### Udemy

```bash
# Configurar cookies (primeira vez)
classroom-setup

# Download como Obsidian, idioma português, arquivo único
classroom-udemy --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --merge --lang pt
```

### DIO (Whisper local em cima dos `.mp4` que você baixou)

> Requer `pip install 'classroom-transcripter[dio]'` + `ffmpeg` no sistema.

```bash
classroom-dio --video-dir ~/dio_videos/jornada-node \
  --whisper-model small --format obsidian --merge
```

### Alura

```bash
classroom-alura --url "https://cursos.alura.com.br/course/docker-fundamentos" \
  --format obsidian --merge
```

### Enriquecer com IA (funciona em qualquer pasta gerada)

```bash
classroom-enrich ./udemy_transcripts/MeuCurso --provider groq
```

## Providers de IA

| Provider | Custo | Velocidade | Setup |
|---|---|---|---|
| **Groq** | Gratuito | Ultra-rápido | [console.groq.com](https://console.groq.com) |
| **Gemini** | Gratuito | Rápido | [aistudio.google.com](https://aistudio.google.com) |
| **Ollama** | Gratuito | Local | `ollama pull llama3.1` |
| **Claude** | Pago | Rápido | [console.anthropic.com](https://console.anthropic.com) |

Veja [`docs/Configuracao.md`](docs/Configuracao.md) pra setup detalhado de cada
um e [`docs/uso.md`](docs/uso.md) pra exemplos de pipeline.

## Arquitetura

Três camadas: `core/` (agnóstico) → `sources/{udemy,dio,alura}/` (plataforma) →
`cli/` (interface).

```
src/classroom_transcripter/
├── core/              # models, formatters, enricher, vtt, downloader (compartilhado)
├── sources/           # udemy/, dio/, alura/ (implementam TranscriptSource)
└── cli/               # um CLI por plataforma + enrich + setup
```

**Regra de ouro:** core não importa de sources. Sources não importam entre si.
Adicionar uma 4ª plataforma (Coursera, Rocketseat) é criar uma `Source` nova
sem mexer no núcleo.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Arquitetura](docs/arquitetura.md) | Como o projeto é organizado |
| [Configuração](docs/Configuracao.md) | Cookies, API keys, `.env` |
| [Uso](docs/uso.md) | Pipeline completo com exemplos |
| [Obsidian](docs/obsidian.md) | Formato, frontmatter dinâmico, queries Dataview |
| [Referência](docs/referencia.md) | Todas as flags + API programática |
| [FAQ](docs/faq.md) | Troubleshooting comum |
| [Changelog](docs/Changelog.md) | Histórico de mudanças |
| [Udemy](docs/sources/udemy.md) | Cookies, API interna, troubleshooting |
| [DIO](docs/sources/dio.md) | Whisper local, ffmpeg, modelos, estrutura dos vídeos |
| [Alura](docs/sources/alura.md) | Como ativar (preencher 3 TODOs) |
| [Plano de Refatoração](docs/refactor-plan.md) | Histórico das 7 fases |

## Testes

```bash
pip install -e '.[dev]'
pytest -v
```

313 testes cobrindo `core/` (downloader, formatters, enricher, modelos, VTT),
`sources/` (Udemy/DIO/Alura) e `cli/`. Mocks de HTTP e Whisper isolam I/O.

## Notas

- **Udemy/Alura:** só funciona com cursos **que você comprou**
- **DIO:** você precisa baixar os `.mp4` separadamente antes de rodar a
  transcrição (a DIO não tem API pública)
- Respeite os termos de uso das plataformas (uso pessoal para estudo)

## Licença

MIT.