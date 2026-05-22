# 🚀 Uso

O pipeline é o mesmo pras 3 plataformas: **download/transcrever → formatar →
enriquecer com IA**. Só o primeiro passo muda por plataforma.

## Estrutura geral dos comandos

```bash
classroom-udemy   [opções]        # Udemy via API + cookies
classroom-dio     [opções]        # DIO via Whisper local
classroom-alura   [opções]        # Alura via login (após Fase 7 ativada)
classroom-enrich  <dir> [opções]  # IA em qualquer pasta gerada
classroom-setup                   # Configurar cookies da Udemy no .env
```

Equivalente via umbrella: `classroom udemy ...`, `classroom enrich ...`, etc.

---

## Udemy

```bash
# Configurar cookies (primeira vez)
classroom-setup

# Listar idiomas disponíveis
classroom-udemy --url "https://udemy.com/course/meu-curso/" --list-langs

# Baixar como texto simples
classroom-udemy --url "https://udemy.com/course/meu-curso/"

# Baixar como Markdown para Obsidian
classroom-udemy --url "https://udemy.com/course/meu-curso/" --format obsidian

# Obsidian + timestamps + arquivo mesclado + idioma
classroom-udemy \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --timestamps --merge --lang pt

# Retomar download interrompido
classroom-udemy --url "https://udemy.com/course/meu-curso/" --resume

# Salvar direto no vault do Obsidian
classroom-udemy \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --output ~/Obsidian/Vault/Cursos
```

---

## DIO

> Requer instalação opcional: `pip install 'classroom-transcripter[dio]'`
> e `ffmpeg` no sistema. Veja [`docs/sources/dio.md`](sources/dio.md).

A DIO transcreve `.mp4` que você baixou manualmente. A estrutura da pasta
DEVE ter subpastas (uma por módulo):

```
~/dio_videos/jornada-node/
├── 01-fundamentos/
│   ├── 01-introducao.mp4
│   └── 02-variaveis.mp4
└── 02-apis/
    └── 01-rest.mp4
```

```bash
# Bootcamp inteiro com Whisper small (padrão)
classroom-dio --video-dir ~/dio_videos/jornada-node --merge

# Qualidade máxima (lento, exige mais RAM)
classroom-dio --video-dir ~/dio_videos/curso --whisper-model medium

# Curso em inglês
classroom-dio --video-dir ~/dio_videos/curso-en --lang en

# Retomar (pula aulas que já viraram .md)
classroom-dio --video-dir ~/dio_videos/curso --resume
```

---

## Alura

> ⚠️ Fase 7 entregue como esqueleto. Veja
> [`docs/sources/alura.md`](sources/alura.md) pra ativar.

```bash
# Credenciais via .env (recomendado)
classroom-alura --url "https://cursos.alura.com.br/course/docker-fundamentos"

# Credenciais via CLI
classroom-alura --url "..." --email e@x.com --ask-password

# Retomar
classroom-alura --url "..." --resume --merge
```

---

## Enriquecimento com IA

Transforma transcrições brutas em notas didáticas: headings com emojis, seções
escaneáveis, callouts do Obsidian, perguntas de revisão. **Funciona em pastas
de qualquer plataforma.**

```bash
# Groq (gratuito, recomendado)
classroom-enrich ./udemy_transcripts/MeuCurso --provider groq

# Groq com modelo mais rápido (limites mais altos)
classroom-enrich ./dio_transcripts/Jornada --provider groq \
  --model llama-3.1-8b-instant

# Groq com delay maior pra não bater rate limit
classroom-enrich ./udemy_transcripts/MeuCurso --provider groq --delay 5

# Gemini (gratuito)
classroom-enrich ./udemy_transcripts/MeuCurso --provider gemini

# Gemini com modelo mais capaz
classroom-enrich ./udemy_transcripts/MeuCurso \
  --provider gemini --model gemini-2.5-pro --delay 10

# Ollama local (gratuito, no seu hardware)
classroom-enrich ./dio_transcripts/Jornada --provider ollama

# Ollama em outra máquina (homelab)
classroom-enrich ./transcripts/X --provider ollama \
  --ollama-url http://192.168.1.100:11434 --model qwen2.5:14b

# Claude (pago, melhor qualidade)
classroom-enrich ./udemy_transcripts/MeuCurso --provider claude

# Preview sem alterar arquivos
classroom-enrich ./udemy_transcripts/MeuCurso --provider groq --dry-run
```

### Comportamento do enricher

- Arquivos já enriquecidos são **pulados automaticamente** (idempotente)
- Se receber rate limit (429), **espera e retenta** automaticamente
- Atingiu limite diário? Rode no dia seguinte — continua de onde parou
- Arquivos especiais (`_MOC.md`, `_index.md`) são ignorados
- Cada arquivo recebe marcador `<!-- enriched-by: provider/model -->`

### Re-enriquecer uma aula

Pra rodar de novo com outro provider ou após atualizar o prompt, delete o
marcador do final do arquivo:

```
<!-- enriched-by: groq/llama-3.3-70b-versatile -->
```

Remova essa linha e rode o `classroom-enrich` novamente.

---

## Pipeline completo (exemplo real)

```bash
# 1. Configurar cookies (uma vez)
classroom-setup

# 2. Baixar e formatar para Obsidian
classroom-udemy \
  --url "https://udemy.com/course/docker-zero-a-profissional/" \
  --format obsidian --merge --lang pt

# 3. Enriquecer com IA
classroom-enrich \
  "./udemy_transcripts/Docker Zero a Profissional" \
  --provider groq --delay 5

# 4. Abrir no Obsidian e estudar 🎉
```

Pra 127 aulas com Groq gratuito (70B), pode levar 2-3 dias por causa dos rate
limits. Dicas:

- Use `--delay 5` pra evitar limite por minuto
- Combine providers: metade Groq, metade Gemini
- Ou use `--model llama-3.1-8b-instant` (limites mais altos)

---

## Pipeline DIO + Ollama (100% local)

Se você tem homelab com Ollama rodando, dá pra fazer tudo offline:

```bash
# 1. Baixe os vídeos do bootcamp pra ~/dio_videos/jornada-node/01-x/, etc

# 2. Transcrever (Whisper local)
classroom-dio --video-dir ~/dio_videos/jornada-node --merge

# 3. Enriquecer (Ollama local)
classroom-enrich ./dio_transcripts/jornada-node \
  --provider ollama --model qwen2.5:14b

# Zero APIs externas, zero limites de uso
```