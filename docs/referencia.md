# 📖 Referência

## Comandos disponíveis

```bash
classroom-udemy    [opções]        # Udemy via API + cookies
classroom-dio      [opções]        # DIO via Whisper local
classroom-alura    [opções]        # Alura via login
classroom-enrich   <dir> [opções]  # IA em qualquer pasta gerada
classroom-setup                    # Configurar cookies da Udemy
classroom <sub>    [opções]        # Umbrella equivalente
```

---

## Flags do `classroom-udemy`

| Flag | Descrição |
|------|-----------|
| `--url`, `-u` | URL ou slug do curso (obrigatório, salvo se `--setup`) |
| `--cookie`, `-c` | Cookie string (opcional se usar `.env`) |
| `--format`, `-f` | Formato: `txt` (padrão) ou `obsidian` |
| `--output`, `-o` | Diretório de saída (padrão: `./udemy_transcripts`) |
| `--lang`, `-l` | Idioma preferido (`pt`, `en`, `es`) |
| `--timestamps`, `-t` | Incluir timestamps `[HH:MM:SS]` |
| `--merge`, `-m` | Gerar arquivo único com todo o curso |
| `--resume`, `-r` | Retomar download interrompido |
| `--list-langs` | Listar idiomas de legenda disponíveis |
| `--setup` | Configurar `.env` interativamente |
| `--debug` | Exibir detalhes das requisições |

## Flags do `classroom-dio`

| Flag | Descrição |
|------|-----------|
| `--video-dir`, `-d` | Pasta raiz do bootcamp baixado (obrigatório) |
| `--whisper-model`, `-w` | `tiny` \| `base` \| `small` (padrão) \| `medium` \| `large` |
| `--lang`, `-l` | Idioma falado (padrão: `pt` ou `.env` WHISPER_LANGUAGE) |
| `--format`, `-f` | Formato: `obsidian` (padrão) ou `txt` |
| `--output`, `-o` | Diretório de saída (padrão: `./dio_transcripts`) |
| `--timestamps`, `-t` | Incluir timestamps `[HH:MM:SS]` |
| `--merge`, `-m` | Arquivo único com todo o curso |
| `--resume`, `-r` | Pular aulas cujo `.md` já existe |
| `--debug` | Exibir stack trace em caso de erro |

## Flags do `classroom-alura`

| Flag | Descrição |
|------|-----------|
| `--url`, `-u` | URL ou slug do curso (obrigatório) |
| `--email`, `-e` | Email de login (padrão: `ALURA_EMAIL` do `.env`) |
| `--password`, `-p` | Senha (padrão: `ALURA_PASSWORD` do `.env`) |
| `--ask-password` | Perguntar a senha interativamente (não vai pro histórico) |
| `--format`, `-f` | Formato: `obsidian` (padrão) ou `txt` |
| `--output`, `-o` | Diretório de saída (padrão: `./alura_transcripts`) |
| `--lang`, `-l` | Idioma default pro `Transcript` (padrão: `pt`) |
| `--timestamps`, `-t` | Incluir timestamps quando disponíveis |
| `--merge`, `-m` | Arquivo único com todo o curso |
| `--resume`, `-r` | Pular aulas cujo `.md` já existe |
| `--debug` | Exibir stack trace em caso de erro |

## Flags do `classroom-enrich`

| Flag | Descrição |
|------|-----------|
| `directory` | Pasta com `.md` gerados pelo download (posicional, obrigatório) |
| `--provider`, `-p` | `ollama` (padrão) \| `groq` \| `gemini` \| `claude` |
| `--model` | Nome do modelo (ex: `llama-3.3-70b-versatile`, `qwen2.5:14b`) |
| `--api-key` | API key (padrão: lê do `.env`) |
| `--ollama-url` | URL do Ollama (padrão: `http://localhost:11434`) |
| `--delay` | Delay entre chamadas em segundos (padrão: `1.0`) |
| `--timeout` | Timeout por request em segundos (padrão: `900`, só relevante pro Ollama) |
| `--dry-run` | Preview sem alterar arquivos |
| `--debug` | Exibir stack trace em caso de erro |

---

## Uso como biblioteca

### Pipeline básico

```python
from classroom_transcripter.sources.udemy import UdemySource
from classroom_transcripter.core.downloader import download_by_identifier
from classroom_transcripter.core.formatters import ObsidianFormatter

source = UdemySource(cookie="access_token=...; cf_clearance=...")
result = download_by_identifier(
    source,
    "https://udemy.com/course/docker-basico/",
    formatter=ObsidianFormatter(platform="udemy"),
    merge=True,
)
print(f"Baixadas: {result.downloaded}/{result.total_lectures}")
```

### Outras plataformas (mesma interface)

```python
# DIO via Whisper local
from classroom_transcripter.sources.dio import DioSource

source = DioSource(whisper_model="small", language="pt")
course = source.fetch_course("/home/joao/dio_videos/jornada-node")

# Alura via login
from classroom_transcripter.sources.alura import AluraSource

source = AluraSource(email="e@x.com", password="senha")
course = source.fetch_course("https://cursos.alura.com.br/course/docker-fund")
```

### Enriquecimento programático

```python
from pathlib import Path
from classroom_transcripter.core.enricher import create_provider, enrich_directory

provider = create_provider("groq", api_key="gsk_...")
result = enrich_directory(
    Path("./udemy_transcripts/MeuCurso"),
    provider,
    delay=2.0,
)
print(f"Enriquecidas: {result.enriched}, puladas: {result.skipped}")
```

### Providers disponíveis

```python
from classroom_transcripter.core.enricher import create_provider

# Groq (gratuito)
provider = create_provider("groq", api_key="gsk_...")

# Gemini (gratuito)
provider = create_provider("gemini", api_key="AIzaSy_...")

# Ollama (local)
provider = create_provider("ollama", model="qwen2.5:14b")

# Claude (pago)
provider = create_provider("claude", api_key="sk-ant-...")

# Modelo customizado
provider = create_provider("groq", model="llama-3.1-8b-instant")
```

---

## API pública

### Imports principais

```python
# Sources (uma por plataforma)
from classroom_transcripter.sources.udemy import UdemySource, UdemyClient, build_course
from classroom_transcripter.sources.dio import DioSource, discover_course, transcribe
from classroom_transcripter.sources.alura import AluraSource, AluraClient

# ABC compartilhada
from classroom_transcripter.sources import TranscriptSource

# Pipeline
from classroom_transcripter.core.downloader import (
    download_course,
    download_by_identifier,
    list_available_captions,
)

# Formatters
from classroom_transcripter.core.formatters import (
    BaseFormatter,
    PlainTextFormatter,
    ObsidianFormatter,
    get_formatter,
)

# Enricher
from classroom_transcripter.core.enricher import (
    LLMProvider,
    create_provider,
    enrich_directory,
    enrich_file,
)

# Modelos
from classroom_transcripter.core.models import (
    Caption,
    Course,
    DownloadResult,
    Lecture,
    Module,
    Transcript,
    TranscriptCue,
)

# Exceptions
from classroom_transcripter.core.exceptions import (
    TranscripterError,
    AuthenticationError,
    CloudflareBlockError,
    CourseNotFoundError,
    TranscriptNotAvailableError,
    NetworkError,
    RateLimitError,
    ParseError,
    ProviderError,
    ProviderAPIKeyMissingError,
)
```

---

## Estrutura do projeto

```
ClassroomTranscripter/
├── src/classroom_transcripter/
│   ├── __init__.py            # Versão + docstring
│   ├── __main__.py            # python -m classroom_transcripter
│   ├── core/                  # Agnóstico de plataforma
│   │   ├── config.py          # .env + constantes
│   │   ├── downloader.py      # Orquestração genérica
│   │   ├── exceptions.py      # TranscripterError + hierarquia
│   │   ├── models.py          # Course, Module, Lecture, Transcript
│   │   ├── platforms.py       # Detecção por URL
│   │   ├── utils.py           # Helpers (slugify, pick_caption)
│   │   ├── vtt.py             # Parser WebVTT
│   │   ├── formatters/        # txt, obsidian
│   │   └── enricher/          # Pipeline + 4 providers
│   ├── sources/
│   │   ├── base.py            # ABC TranscriptSource
│   │   ├── udemy/             # Source + client + parser
│   │   ├── dio/               # Source + video_finder + whisper_engine
│   │   └── alura/             # Source + client (3 TODOs) + parser
│   └── cli/
│       ├── main.py            # Umbrella `classroom <sub>`
│       ├── udemy_cli.py
│       ├── dio_cli.py
│       ├── alura_cli.py
│       ├── enrich_cli.py
│       └── setup_cli.py
├── tests/
│   ├── core/                  # config, models, platforms, utils, vtt, formatters, enricher, downloader
│   ├── sources/{udemy,dio,alura}/
│   ├── cli/
│   └── test_structure.py      # Sanity check da arquitetura
├── docs/
│   ├── arquitetura.md
│   ├── refactor-plan.md
│   ├── Configuracao.md
│   ├── uso.md
│   ├── obsidian.md
│   ├── referencia.md          # ← este arquivo
│   ├── faq.md
│   ├── Changelog.md
│   └── sources/
│       ├── udemy.md
│       ├── dio.md
│       └── alura.md
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```