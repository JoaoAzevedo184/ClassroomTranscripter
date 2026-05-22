# DIO

> **Status:** 100% funcional. Usa Whisper local — não depende de API da DIO.

A DIO (Digital Innovation One) não tem API pública pra acessar transcrições.
A solução é baixar os `.mp4` manualmente (via outra ferramenta) e usar
[OpenAI Whisper](https://github.com/openai/whisper) local pra gerar as
transcrições.

## Como funciona

1. Você baixa os `.mp4` do bootcamp manualmente e organiza em subpastas por
   módulo
2. **`video_finder`** (`sources/dio/video_finder.py`) — descobre a estrutura
   do curso a partir dos arquivos no disco
3. **`whisper_engine`** (`sources/dio/whisper_engine.py`) — wrapper do Whisper
   que converte `.mp4` → `Transcript` com cues
4. **`DioSource`** (`sources/dio/source.py`) — implementa `TranscriptSource`,
   `authenticate()` é no-op porque é tudo local

## Pré-requisitos

### Instalação Python

```bash
pip install 'classroom-transcripter[dio]'
```

Isso instala `openai-whisper`, `torch` e `ffmpeg-python`.

### ffmpeg do sistema

```bash
sudo apt install ffmpeg          # Ubuntu/Pop!_OS/Debian
sudo dnf install ffmpeg          # Fedora
brew install ffmpeg              # macOS
```

Confirme: `ffmpeg -version` deve funcionar no shell.

### GPU (opcional, mas recomendado)

Se você tem GPU NVIDIA com CUDA, o Whisper detecta automaticamente via
PyTorch e roda **10-20x mais rápido**. Sem GPU, ele cai em CPU.

```bash
# Confirme se PyTorch enxerga sua GPU
python -c "import torch; print(torch.cuda.is_available())"
```

## Estrutura obrigatória dos vídeos

Diferente da Udemy/Alura, a DIO **não tem URL nem slug** — o "curso" é uma
pasta no seu disco. A estrutura DEVE ter subpastas (uma por módulo):

```
~/dio_videos/jornada-node/         ← raiz do bootcamp
├── 01-fundamentos/                ← módulo
│   ├── 01-introducao.mp4          ← aula
│   ├── 02-variaveis.mp4
│   └── 03-funcoes.mp4
├── 02-apis/
│   ├── 01-intro-rest.mp4
│   └── 02-express.mp4
└── 03-banco-de-dados/
    ├── 01-sql.mp4
    └── 02-orm.mp4
```

> ❌ **Estrutura plana NÃO é suportada** (todos os `.mp4` direto na raiz).
> O `video_finder` lança erro com instruções. Isso é proposital — força você a
> organizar o material antes de transcrever, e o `Module` reflete a estrutura
> que vai aparecer no Obsidian.

### Convenções da estrutura

- **Ordem natural** — `01-`, `02-`, ..., `10-` são ordenados corretamente
  (não como string)
- **Prefixo numérico** — `01-introducao.mp4` vira título "Introducao"
- **Separadores** — hífen (`-`), underscore (`_`) e espaço são equivalentes
- **Extensões aceitas** — `.mp4`, `.mkv`, `.webm`, `.mov`, `.m4a`, `.mp3`, `.wav`
- **Subpastas vazias** — ignoradas automaticamente

## Configuração

`.env`:

```env
DIO_VIDEO_DIR=./dio_videos        # Pasta raiz default
WHISPER_MODEL=small               # tiny|base|small|medium|large
WHISPER_LANGUAGE=pt
```

## Uso

### Transcrever um bootcamp inteiro

```bash
classroom-dio --video-dir ~/dio_videos/jornada-node --merge
```

### Escolher modelo Whisper

```bash
# Mais rápido, qualidade menor
classroom-dio --video-dir ./curso --whisper-model tiny

# Padrão recomendado
classroom-dio --video-dir ./curso --whisper-model small

# Qualidade máxima (lento, exige mais RAM)
classroom-dio --video-dir ./curso --whisper-model medium
```

### Outros idiomas

```bash
classroom-dio --video-dir ./curso-ingles --lang en
classroom-dio --video-dir ./curso-espanhol --lang es
```

### Retomar transcrição interrompida

Transcrição com Whisper é **lenta** (especialmente sem GPU). O `--resume` pula
aulas cujo arquivo `.md` já foi gerado:

```bash
classroom-dio --video-dir ./curso --resume
```

> 💡 Não existe cache em disco do output do Whisper. O `--resume` cobre o caso
> de retomada depois de `Ctrl+C` ou crash — se o `.md` foi salvo, não
> retranscreve.

## Modelos Whisper

| Modelo | Tamanho | RAM | Velocidade (CPU) | Velocidade (GPU) | Qualidade |
|--------|:---:|:---:|:---:|:---:|:---:|
| tiny | ~75MB | ~1GB | ~10x realtime | ~30x | ⭐⭐ |
| base | ~140MB | ~1GB | ~7x | ~20x | ⭐⭐⭐ |
| **small** | ~460MB | ~2GB | ~4x | ~15x | ⭐⭐⭐⭐ |
| medium | ~1.5GB | ~5GB | ~2x | ~8x | ⭐⭐⭐⭐ |
| large | ~3GB | ~10GB | ~1x | ~5x | ⭐⭐⭐⭐⭐ |

"~Nx realtime" significa que transcrever 1 hora de vídeo leva ~1/N hora.

**Pesos baixados em:** `~/.cache/whisper/` (compartilhado entre execuções).

## Saída

```
dio_transcripts/jornada-node/
├── _MOC.md
├── _CURSO_COMPLETO.md             # (com --merge)
├── _metadata.json
├── 01 - Fundamentos/
│   ├── _index.md
│   ├── 001 - Introducao.md
│   ├── 002 - Variaveis.md
│   └── 003 - Funcoes.md
└── 02 - Apis/
    ├── _index.md
    └── 001 - Intro Rest.md
```

Frontmatter inclui `platform: dio` — facilita filtrar no Dataview.

## Como funciona internamente

```
~/dio_videos/jornada-node/  →  video_finder.discover_course
                                       ↓
                                Course (platform=dio)
                                       ↓ (pra cada Lecture)
                              lecture.metadata["file"]
                                       ↓
                          whisper_engine.transcribe
                                       ↓ (whisper.load_model + transcribe)
                              Transcript com cues
```

O modelo Whisper é carregado **uma vez por execução** via `lru_cache` em
memória. Entre execuções, os pesos vêm do cache padrão do Whisper.

## Truque: usar DIO source pra qualquer curso

`DioSource` não é específico da DIO — funciona com **qualquer pasta de
vídeos**. Útil quando:

- O curso da Udemy não tem captions (instrutor não habilitou)
- Você tem aulas em `.mp4` de outras fontes (YouTube, gravações próprias)
- Quer reprocessar transcrições oficiais que ficaram ruins

Basta organizar os vídeos na estrutura profunda obrigatória e rodar
`classroom-dio`. O `platform: dio` no frontmatter é cosmético — você pode
editar manualmente se quiser.

## Troubleshooting

### `Whisper não instalado`

```bash
pip install 'classroom-transcripter[dio]'
```

### `FileNotFoundError: ffmpeg`

Instale ffmpeg do sistema (não vem com pip):

```bash
sudo apt install ffmpeg          # Linux
brew install ffmpeg              # macOS
```

### `Pasta não contém subpastas de módulos`

Estrutura plana não é suportada. Crie subpastas:

```bash
cd ~/dio_videos/meu-curso
mkdir 01-modulo
mv *.mp4 01-modulo/
```

### `GPU out of memory`

Modelo grande demais pra placa. Use menor:

```bash
classroom-dio --video-dir ./curso --whisper-model small  # em vez de medium
```

### Whisper transcreve mas qualidade é péssima

- Verifique o `--lang` (Whisper detecta automaticamente, mas explicitar ajuda)
- Use modelo maior: `small` → `medium`
- Áudio com música de fundo, eco ou má qualidade resulta em transcrições piores
  — Whisper não faz milagre

### Whisper trava ou roda 100% CPU sem GPU

CPU puro é lento mesmo (~4x realtime no small). Pra 10 horas de aulas, espere
~2.5h de transcrição. Use `--whisper-model tiny` se a qualidade for aceitável
pra prototipar.

## API programática

```python
from classroom_transcripter.sources.dio import DioSource
from classroom_transcripter.core.downloader import download_by_identifier
from classroom_transcripter.core.formatters import ObsidianFormatter

source = DioSource(whisper_model="small", language="pt")

result = download_by_identifier(
    source,
    "/home/joao/dio_videos/jornada-node",  # identifier = path
    formatter=ObsidianFormatter(platform="dio"),
    merge=True,
    resume=True,
)

print(f"Transcritas: {result.downloaded}/{result.total_lectures}")
```

### Transcrever um único arquivo

```python
from pathlib import Path
from classroom_transcripter.sources.dio import transcribe

transcript = transcribe(
    Path("/home/joao/aula.mp4"),
    lecture_id="aula-1",
    model_name="small",
    language="pt",
)

print(transcript.plain_text)
for cue in transcript.cues:
    print(f"[{cue.start_seconds:.1f}s] {cue.text}")
```