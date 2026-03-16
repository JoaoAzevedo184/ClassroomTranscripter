# 🎓 Udemy Transcripter

Ferramenta CLI que extrai transcrições de cursos da Udemy e transforma em material de estudo com IA.

**Pipeline:** `download` → `format` → `enrich`

```bash
# 1. Baixa as transcrições e formata para Obsidian
python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --format obsidian

# 2. Enriquece com IA (código, exemplos, estrutura educativa)
python -m udemy_transcripter --enrich ./udemy_transcripts/MeuCurso --provider ollama
```

## Instalação

```bash
git clone https://github.com/JoaoAzevedo184/UdemyTranscripter.git
cd UdemyTranscripter
pip install -e .
```

## Configuração

O projeto usa um arquivo `.env` na raiz para armazenar credenciais. Rode `--setup` para criá-lo interativamente, ou copie o `.env.example` e preencha manualmente.

```bash
cp .env.example .env
```

### Cookies da Udemy (obrigatório para download)

Os cookies autenticam suas requisições à API da Udemy.

**Como obter:**

1. Acesse [udemy.com](https://udemy.com) e faça login
2. Abra o **DevTools** (`F12`) → aba **Network**
3. Recarregue a página de qualquer curso
4. Clique em alguma requisição para `www.udemy.com`
5. Em **Request Headers**, copie o valor completo do header **`Cookie`**

**Configurar via setup interativo:**

```bash
python -m udemy_transcripter --setup
# Cole a cookie string quando solicitado
```

**Ou configure manualmente no `.env`:**

```env
UDEMY_COOKIES='access_token=xxx; cf_clearance=yyy; client_id=zzz; ...'
```

> ⚠️ Nunca compartilhe seus cookies. Eles dão acesso à sua conta.
> Cookies expiram periodicamente — se der erro 403, gere novos.

### API Key da Anthropic (opcional — apenas para enriquecimento com Claude)

Necessário **somente** se quiser usar o Claude como provider de IA no `--enrich`. Se usar Ollama (local), não precisa de API key.

**Como obter:**

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Crie uma conta ou faça login
3. Vá em **Settings** → **API Keys** → **Create Key**
4. Copie a chave gerada (começa com `sk-ant-`)

> ⚠️ A chave só é exibida uma vez. Guarde em lugar seguro.

**Adicione ao `.env`:**

```env
UDEMY_COOKIES='sua_cookie_string_aqui'
ANTHROPIC_API_KEY=sk-ant-api03-sua-chave-aqui
```

**Ou passe diretamente na CLI (sem salvar no `.env`):**

```bash
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider claude \
  --api-key sk-ant-api03-sua-chave-aqui
```

**Ordem de resolução da API key:**

| Prioridade | Fonte |
|:---:|---|
| 1 | Flag `--api-key` na CLI |
| 2 | `ANTHROPIC_API_KEY` no `.env` |
| 3 | Variável de ambiente `ANTHROPIC_API_KEY` do sistema |

**Modelos disponíveis:**

| Modelo | Velocidade | Qualidade | Custo |
|--------|:---:|:---:|:---:|
| `claude-sonnet-4-20250514` (padrão) | Médio | Alta | ~$3/MTok |
| `claude-haiku-4-5-20251001` | Rápido | Boa | ~$1/MTok |
| `claude-opus-4-6` | Lento | Máxima | ~$15/MTok |

Custo estimado para um curso com ~100 aulas: **$0.50–$2.00** com Sonnet.

## Uso

### Download de transcrições

```bash
# Listar idiomas disponíveis
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" --list-langs

# Baixar como texto simples
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/"

# Baixar como Markdown para Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" --format obsidian

# Obsidian + timestamps + arquivo mesclado + idioma
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --timestamps --merge --lang pt

# Salvar direto no vault do Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --output ~/Obsidian/Vault/Cursos
```

### Enriquecimento com IA

Transforma transcrições brutas em material de estudo completo: blocos de código, exemplos práticos, estrutura educativa e perguntas de revisão.

```bash
# Com Ollama (local, gratuito)
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider ollama

# Com modelo específico do Ollama
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider ollama --model qwen2.5:14b

# Com Claude API (precisa de ANTHROPIC_API_KEY)
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider claude

# Com Claude e modelo econômico
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider claude --model claude-haiku-4-5-20251001

# Preview sem alterar nenhum arquivo
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider ollama --dry-run

# Ollama rodando em outra máquina da rede
python -m udemy_transcripter \
  --enrich ./udemy_transcripts/MeuCurso \
  --provider ollama --ollama-url http://192.168.1.100:11434
```

**Comparação de providers:**

| | Ollama | Claude |
|---|---|---|
| **Custo** | Gratuito | ~$0.50–2.00/curso |
| **Privacidade** | 100% local | Dados vão para a API |
| **Velocidade** | Depende do hardware | Rápido |
| **Qualidade** | Boa (modelos 7B+) | Excelente |
| **Setup** | `ollama pull llama3.1` | API key no `.env` |

**Comportamento do enricher:**

- Arquivos já enriquecidos são **pulados automaticamente** (idempotente)
- Arquivos especiais (`_MOC.md`, `_index.md`) são ignorados
- Frontmatter YAML, navegação e anotações são preservados
- Cada arquivo recebe marcador `<!-- enriched-by: provider/model -->`
- Se interrompido, rode novamente — continua de onde parou

### Pipeline completo (exemplo real)

```bash
# 1. Configurar cookies (uma vez)
python -m udemy_transcripter --setup

# 2. Baixar e formatar para Obsidian
python -m udemy_transcripter \
  --url "https://udemy.com/course/docker-zero-a-profissional/" \
  --format obsidian --merge --lang pt

# 3. Enriquecer com IA
python -m udemy_transcripter \
  --enrich "./udemy_transcripts/Docker Zero a Profissional" \
  --provider ollama --model llama3.1

# 4. Abrir no Obsidian e estudar 🎉
```

## Formato Obsidian (`--format obsidian`)

### Saída do download

- **Frontmatter YAML** — funciona com Dataview
- **Tags automáticas** — `#udemy`, `#curso/nome`, `#secao/nome`
- **Navegação** — wikilinks `⬅ [[anterior]] | [[próxima]] ➡`
- **MOC** — `_MOC.md` com links para todas as notas
- **Índice por seção** — `_index.md` com lista numerada
- **Área de anotações** — espaço reservado para notas pessoais

### Após enriquecimento

- **TL;DR** — resumo em 3-4 bullet points
- **Headings educativos** — conceito → explicação → exemplo
- **Blocos de código** — condizentes com a tecnologia da aula
- **Callouts** — `> [!tip]`, `> [!warning]`, `> [!example]`, `> [!question]`
- **Pontos-chave** — 3-5 bullet points de revisão
- **Perguntas de revisão** — 2-3 perguntas para fixação

### Estrutura de saída

```
udemy_transcripts/
└── Docker Zero a Profissional/
    ├── _MOC.md
    ├── _CURSO_COMPLETO.md          # (com --merge)
    ├── _metadata.json
    ├── 01 - Primeiros Passos/
    │   ├── _index.md
    │   ├── 014 - Instalando o Docker.md
    │   └── 015 - O que sao Containers.md
    └── 02 - Construindo Imagens/
        ├── _index.md
        ├── 027 - Entendendo Layers.md
        └── 028 - Criando seu primeiro Dockerfile.md
```

## Uso como biblioteca

```python
from udemy_transcripter import (
    UdemyClient,
    download_transcripts,
    ObsidianFormatter,
)
from udemy_transcripter.enricher import create_provider, enrich_directory
from pathlib import Path

# Download
client = UdemyClient("access_token=...; cf_clearance=...")
result = download_transcripts(
    client,
    slug="docker-basico",
    formatter=ObsidianFormatter(),
    merge=True,
)

# Enriquecimento
provider = create_provider("ollama", model="llama3.1")
enrich_directory(Path(result.output_dir), provider)
```

## Referência de opções

### Download

| Flag | Descrição |
|------|-----------|
| `--url`, `-u` | URL ou slug do curso |
| `--format`, `-f` | Formato: `txt` (padrão) ou `obsidian` |
| `--output`, `-o` | Diretório de saída (padrão: `./udemy_transcripts`) |
| `--lang`, `-l` | Idioma preferido (`pt`, `en`, `es`) |
| `--timestamps`, `-t` | Incluir timestamps `[HH:MM:SS]` |
| `--merge`, `-m` | Gerar arquivo único com todo o curso |
| `--list-langs` | Listar idiomas disponíveis |
| `--cookie`, `-c` | Cookie string (opcional se usar `.env`) |

### Enriquecimento com IA

| Flag | Descrição |
|------|-----------|
| `--enrich DIR` | Diretório com notas `.md` para enriquecer |
| `--provider` | `ollama` (padrão) ou `claude` |
| `--model` | Modelo (ex: `llama3.1`, `claude-sonnet-4-20250514`) |
| `--api-key` | API key da Anthropic (ou use `.env`) |
| `--ollama-url` | URL do Ollama (padrão: `http://localhost:11434`) |
| `--delay` | Delay entre chamadas em segundos (padrão: `1.0`) |
| `--dry-run` | Preview sem alterar arquivos |

### Geral

| Flag | Descrição |
|------|-----------|
| `--setup` | Configurar `.env` interativamente |
| `--debug` | Exibir detalhes das requisições |

## Estrutura do projeto

```
udemy_transcripter/
├── udemy_transcripter/        # Pacote principal
│   ├── __init__.py            # API pública
│   ├── __main__.py            # python -m udemy_transcripter
│   ├── cli.py                 # Interface de linha de comando
│   ├── client.py              # Cliente HTTP (Cloudflare bypass)
│   ├── config.py              # Constantes e carregamento de .env
│   ├── downloader.py          # Download e salvamento
│   ├── enricher.py            # Enriquecimento com IA (Ollama / Claude)
│   ├── exceptions.py          # Exceções customizadas
│   ├── formatters.py          # Formatadores (txt, obsidian)
│   ├── models.py              # Dataclasses do domínio
│   ├── setup.py               # Configuração interativa do .env
│   ├── utils.py               # Funções utilitárias
│   └── vtt.py                 # Parser de legendas WebVTT
├── tests/                     # 63 testes unitários
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_enricher.py
│   ├── test_formatters.py
│   ├── test_utils.py
│   └── test_vtt.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Testes

```bash
pip install -e ".[dev]"
pytest -v
```

## Notas

- Só funciona com cursos **que você comprou**
- Depende das legendas/captions disponibilizadas pelo instrutor
- Aulas sem legenda (quizzes, exercícios, artigos) são puladas
- Cookies expiram — se der 403, copie novos do navegador
- Respeite os termos de uso da Udemy (uso pessoal para estudo)