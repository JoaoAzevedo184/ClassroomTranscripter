# Udemy

> **Status:** 100% funcional desde a v0.1. Esta é a plataforma de referência —
> as outras (DIO, Alura) seguem o mesmo padrão de saída.

A Udemy expõe uma API interna (não documentada publicamente) protegida por
Cloudflare e autenticada via cookies de sessão. O `UdemyClient` usa
[`curl_cffi`](https://github.com/lexiforest/curl_cffi) pra imitar o TLS
fingerprint do Chrome e passar pela proteção.

## Como funciona

1. **Cliente HTTP** (`sources/udemy/client.py`) — fala com a API interna
2. **Parser** (`sources/udemy/parser.py`) — monta `Course` a partir das
   respostas da API
3. **Source** (`sources/udemy/source.py`) — implementa `TranscriptSource`
   integrando client + parser + `core.vtt`

## Pré-requisitos

- Conta na Udemy logada no navegador
- Curso comprado (com legendas habilitadas pelo instrutor)
- Cookies copiados do DevTools

## Configuração

### Via setup interativo (recomendado)

```bash
classroom-setup
# (Cola a cookie string quando solicitado)
```

### Manualmente no `.env`

```env
UDEMY_COOKIES='access_token=xxx; cf_clearance=yyy; client_id=zzz; ...'
```

### Como obter os cookies

1. Acesse [udemy.com](https://udemy.com) logado
2. **F12** → aba **Network**
3. Recarregue qualquer página do curso
4. Clique em uma request pra `www.udemy.com`
5. Em **Request Headers**, copie o valor completo do header **`Cookie`**

> ⚠️ A cookie string deve conter pelo menos `access_token=` e `cf_clearance=`.
> Sem `cf_clearance`, você cai no challenge do Cloudflare.

## Uso

### Listar idiomas disponíveis

```bash
classroom-udemy --url "https://udemy.com/course/docker-basico/" --list-langs
```

Saída:

```
🎓 Docker - Zero a Profissional
  Idiomas disponíveis:
    • Português (pt) — 127 aulas
    • English (en) — 127 aulas
```

### Download básico

```bash
# Texto simples
classroom-udemy --url "https://udemy.com/course/docker-basico/"

# Obsidian
classroom-udemy --url "https://udemy.com/course/docker-basico/" --format obsidian
```

### Download avançado

```bash
classroom-udemy \
  --url "https://udemy.com/course/docker-basico/" \
  --format obsidian \
  --timestamps \
  --merge \
  --lang pt \
  --output ~/Obsidian/Cursos
```

### Retomar download interrompido

```bash
classroom-udemy --url "..." --resume
```

O `--resume` pula aulas cujo arquivo `.md`/`.txt` já existe em disco. Útil pra:

- Retomar após `Ctrl+C`
- Re-rodar depois de cookies expirados (sem refazer aulas já baixadas)
- Adicionar `--merge` depois (carrega o conteúdo já em disco)

## Saída

```
udemy_transcripts/Docker Zero a Profissional/
├── _MOC.md                              # Map of Content (Obsidian)
├── _CURSO_COMPLETO.md                   # Tudo num arquivo (com --merge)
├── _metadata.json
├── 01 - Primeiros Passos/
│   ├── _index.md
│   ├── 014 - Instalando o Docker.md
│   └── 015 - O que sao Containers.md
└── 02 - Construindo Imagens/
    ├── _index.md
    └── 027 - Entendendo Layers.md
```

A numeração `001`, `002`, `014` é o `object_index` da API da Udemy — itens sem
legenda (quizzes, exercícios) são pulados, então **buracos na numeração são
esperados**.

## Como funciona internamente

```
URL → UdemyPlatform.extract_slug → slug
slug → UdemyClient.get_course_info → (course_id, title)
course_id → UdemyClient.get_curriculum → list[Module]
                                          ↓ (pra cada Lecture)
                                       Caption[]
                                          ↓ (pick_caption por LANG_PRIORITY)
                                       Caption escolhida
                                          ↓ (HTTP GET na URL do VTT)
                                       texto WebVTT
                                          ↓ (core.vtt.vtt_to_transcript)
                                       Transcript com cues
```

O cliente usa **dois HTTP clients diferentes** por design:

- **`curl_cffi`** pras chamadas à API da Udemy (precisa do TLS fingerprint
  Chrome pra passar pelo Cloudflare)
- **`requests`** padrão pra baixar VTTs (servidos por CDNs sem proteção)

## Troubleshooting

### `403 Just a moment...`

Cloudflare bloqueou. Possíveis causas:

1. Cookies expirados → `classroom-setup`
2. Curso não comprado → confirme no painel da Udemy
3. `cf_clearance` ausente → copie a cookie **completa**, não só `access_token`

```bash
# Debug detalhado
classroom-udemy --url "..." --list-langs --debug
```

### `401 Unauthorized`

Token inválido. Gere novos cookies.

### Cookies truncados ao colar

Terminais ocasionalmente truncam strings longas com `…` (U+2026). O cliente
remove non-ASCII automaticamente, mas se truncar antes do `access_token`, dá
ruim. Alternativas:

- Cole direto no `.env` com um editor de texto
- Use `--cookie` passando a string entre aspas duplas

### `Nenhuma legenda disponível`

O instrutor não habilitou captions. Não há solução via Udemy API.

> 💡 Alternativa criativa: baixe os vídeos com outra ferramenta e use
> `classroom-dio` (Whisper local) pra transcrever. A DIO source funciona em
> qualquer `.mp4`, não só em vídeos da DIO.

## API programática

```python
from classroom_transcripter.sources.udemy import UdemySource
from classroom_transcripter.core.downloader import download_by_identifier
from classroom_transcripter.core.formatters import ObsidianFormatter

source = UdemySource(cookie="access_token=...; cf_clearance=...")
source.authenticate()  # valida o cookie via /users/me

result = download_by_identifier(
    source,
    "https://udemy.com/course/docker-basico/",
    formatter=ObsidianFormatter(platform="udemy"),
    merge=True,
    lang="pt",
)

print(f"Baixadas: {result.downloaded}")
```

### Acessar a estrutura do curso sem baixar

```python
source = UdemySource(cookie="...")
course = source.fetch_course("docker-basico")

for module in course.modules:
    print(f"## {module.title}")
    for lecture in module.lectures:
        langs = [c.locale for c in lecture.captions]
        print(f"  {lecture.object_index:03d} - {lecture.title} ({langs})")
```