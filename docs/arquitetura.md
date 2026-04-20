# Arquitetura

O Classroom Transcripter é dividido em **três camadas** com fronteiras bem definidas:

```
┌─────────────────────────────────────────────────┐
│  CLI                                            │
│  (classroom-udemy, classroom-dio, ...)          │
├─────────────────────────────────────────────────┤
│  Sources  (udemy, dio, alura)                   │
│  ↑ implementam TranscriptSource                 │
├─────────────────────────────────────────────────┤
│  Core  (models, formatters, enricher, vtt)      │
│  ↑ agnóstico de plataforma                      │
└─────────────────────────────────────────────────┘
```

## Regra de ouro

> **Core não importa de Sources. Sources não importam entre si.**
> CLI pode importar de ambos.

Se você se pegar escrevendo `from classroom_transcripter.sources.udemy import X` dentro de `core/`, é sinal de que o código tá no lugar errado.

## Camada `core/`

Tudo que é **agnóstico de plataforma**. Modelos de domínio, utilitários, parser de VTT, formatadores e enricher.

| Módulo | Responsabilidade |
|---|---|
| `models.py` | Dataclasses `Course`, `Module`, `Lecture`, `Transcript`, `TranscriptCue`, `DownloadResult` |
| `config.py` | Carrega `.env`, expõe constantes |
| `exceptions.py` | Hierarquia de erros (raiz `TranscripterError`) |
| `utils.py` | `slugify`, paths, helpers genéricos |
| `vtt.py` | Parser WebVTT → `list[TranscriptCue]` |
| `formatters/` | `TxtFormatter`, `ObsidianFormatter` (ambos herdam `BaseFormatter`) |
| `enricher/` | Orquestração + providers de IA (Groq/Gemini/Ollama/Claude) |

## Camada `sources/`

Cada subpacote implementa a ABC `TranscriptSource` (em `sources/base.py`).

| Source | `fetch_course` recebe | `fetch_transcript` usa |
|---|---|---|
| `UdemySource` | URL ou slug | API Udemy + VTT |
| `DioSource` | path local da pasta | Whisper local (.mp4 → texto) |
| `AluraSource` | URL ou slug | API/scraping da Alura |

Os três devolvem os **mesmos tipos** (`Course`, `Transcript`) — é isso que permite o resto do pipeline ser compartilhado.

## Camada `cli/`

Um executável por plataforma + o `enrich` agnóstico. O umbrella (`classroom`) é só um dispatcher.

```
classroom udemy  → cli/udemy_cli.py
classroom dio    → cli/dio_cli.py
classroom alura  → cli/alura_cli.py
classroom enrich → cli/enrich_cli.py
```

## Fluxo de uma execução típica

Exemplo: `classroom-udemy --url ... --format obsidian --merge`

```
udemy_cli.main()
    ├─ parse args
    ├─ source = UdemySource(cookie=...)          ← sources/udemy/
    ├─ source.authenticate()
    ├─ course = source.fetch_course(url)         ← retorna core.models.Course
    ├─ formatter = get_formatter("obsidian")     ← core/formatters/
    └─ for lecture in course.iter_lectures():
         transcript = source.fetch_transcript(lecture)  ← retorna core.models.Transcript
         formatter.write_lecture(lecture, transcript, output_path)
```

Repare: **o loop não sabe** que tá falando com Udemy. Troca `UdemySource` por `DioSource` e tudo continua funcionando — é essa a propriedade que a refatoração desbloqueia.

## Como adicionar uma nova plataforma (futuro)

Digamos que apareça uma 4ª plataforma (Coursera, por exemplo):

1. Criar `sources/coursera/` com `source.py`, `client.py`, `parser.py`
2. `CourseraSource(TranscriptSource)` implementa os 3 métodos abstratos
3. Criar `cli/coursera_cli.py`
4. Registrar entry point `classroom-coursera` em `pyproject.toml`

**Nada no `core/` precisa mudar.**
