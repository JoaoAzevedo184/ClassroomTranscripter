# 🎓 Udemy Transcripter

Ferramenta CLI em Python para extrair transcrições/legendas de cursos que você comprou na Udemy.

## Requisitos

- Python 3.10+
- `curl_cffi` — necessário para bypass do Cloudflare
- `requests`
- `python-dotenv`

## Instalação

```bash
# Clone o repositório
git clone https://github.com/JoaoAzevedo184/UdemyTranscripter.git
cd UdemyTranscripter

# Instale as dependências
pip install -e .

# Ou apenas as dependências sem instalar o pacote
pip install -r requirements.txt
```

## Configuração inicial

### 1. Obtenha os cookies do navegador

1. Acesse [udemy.com](https://udemy.com) e faça login
2. Abra o **DevTools** do navegador (`F12`)
3. Vá na aba **Network** e recarregue a página
4. Clique em alguma requisição para `www.udemy.com`
5. Em **Request Headers**, copie o valor completo do header **`Cookie`**

> ⚠️ **Nunca compartilhe seus cookies.** Eles dão acesso à sua conta.
> Os cookies expiram periodicamente — se der erro 403, gere novos.

### 2. Configure o `.env` (recomendado)

```bash
# Setup interativo — cria o .env e o .gitignore automaticamente
python -m udemy_transcripter --setup
```

Ou crie manualmente um arquivo `.env`:

```env
UDEMY_COOKIES='access_token=xxx; cf_clearance=yyy; client_id=zzz; ...'
```

## Uso

```bash
# Listar idiomas disponíveis
python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --list-langs

# Baixar como texto simples (padrão)
python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/"

# Baixar como Markdown para Obsidian
python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --format obsidian

# Obsidian + timestamps + arquivo mesclado
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --timestamps --merge

# Combinar opções
python -m udemy_transcripter \
  --url "https://udemy.com/course/meu-curso/" \
  --format obsidian --lang pt --output ~/Obsidian/Vault/Cursos

# Depurar problemas
python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --debug
```

> Todos os comandos assumem que o cookie está no `.env`. Se preferir, passe `--cookie 'SUA_STRING'`.

## Formato Obsidian (`--format obsidian`)

Gera notas `.md` otimizadas para estudo no Obsidian:

- **Frontmatter YAML** com `course`, `section`, `tags`, `date` — funciona com Dataview
- **Tags automáticas**: `#udemy`, `#curso/nome-do-curso`, `#secao/nome-da-secao`
- **Navegação entre aulas** com wikilinks `[[anterior]]` / `[[próxima]]`
- **MOC (Map of Content)** com links para todas as notas do curso
- **Índice por seção** com lista numerada de aulas
- **Área de anotações** em cada nota para você escrever durante o estudo
- **Parágrafos formatados** para leitura confortável (sem paredes de texto)

### Estrutura gerada no Obsidian

```
Vault/
└── Cursos/
    └── Docker Zero a Profissional/
        ├── _MOC.md                           # Map of Content do curso
        ├── _metadata.json
        ├── _CURSO_COMPLETO.md                # (com --merge)
        ├── 01 - Introdução/
        │   ├── _index.md                     # Índice da seção
        │   ├── 001 - Bem-vindo.md
        │   └── 002 - Configuração.md
        └── 02 - Docker Basics/
            ├── _index.md
            ├── 003 - O que é Docker.md
            └── 004 - Containers.md
```

### Exemplo de nota gerada

```markdown
---
course: "Docker Zero a Profissional"
section: "Introdução"
lecture: 1
udemy_id: 47385507
date: 2026-03-15
tags:
  - udemy
  - curso/docker-zero-a-profissional
  - secao/introdução
---

# Bem-vindo ao Curso

> [!tip] Navegação
> [[002 - Configuração do Ambiente|Próxima]] ➡

## Transcrição

Olá, bem-vindos ao curso de Docker. Neste curso vocês vão aprender...

---

## Anotações

> [!note] Espaço para suas anotações
>
```

## Uso como biblioteca

```python
from udemy_transcripter import UdemyClient, download_transcripts, ObsidianFormatter

client = UdemyClient("access_token=...; cf_clearance=...")

# Texto simples
result = download_transcripts(client, slug="docker-basico", merge=True)

# Obsidian
result = download_transcripts(
    client, slug="docker-basico",
    formatter=ObsidianFormatter(), merge=True,
)
print(f"Baixadas {result.downloaded} transcrições")
```

## Estrutura do projeto

```
udemy_transcripter/
├── udemy_transcripter/        # Pacote principal
│   ├── __init__.py            # API pública
│   ├── __main__.py            # Entry point: python -m udemy_transcripter
│   ├── cli.py                 # Interface de linha de comando
│   ├── client.py              # Cliente HTTP (Cloudflare bypass)
│   ├── config.py              # Constantes e carregamento de .env
│   ├── downloader.py          # Lógica de download e salvamento
│   ├── exceptions.py          # Exceções customizadas
│   ├── formatters.py          # Formatadores de saída (txt, obsidian)
│   ├── models.py              # Dataclasses do domínio
│   ├── setup.py               # Configuração interativa do .env
│   ├── utils.py               # Funções utilitárias
│   └── vtt.py                 # Parser de legendas WebVTT
├── tests/                     # Testes unitários (46 testes)
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_formatters.py
│   ├── test_utils.py
│   └── test_vtt.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Opções

| Flag | Descrição |
|------|-----------|
| `--setup` | Criar/atualizar `.env` interativamente |
| `--cookie`, `-c` | Cookie string do navegador (opcional se usar `.env`) |
| `--url`, `-u` | URL ou slug do curso **(obrigatório)** |
| `--format`, `-f` | Formato de saída: `txt` (padrão) ou `obsidian` |
| `--output`, `-o` | Diretório de saída (padrão: `./udemy_transcripts`) |
| `--lang`, `-l` | Idioma preferido (`pt`, `en`, `es`, etc.) |
| `--timestamps`, `-t` | Incluir timestamps `[HH:MM:SS]` no texto |
| `--merge`, `-m` | Gerar arquivo único com todo o curso |
| `--list-langs` | Apenas listar idiomas disponíveis |
| `--debug` | Exibir detalhes das requisições para depuração |

## Testes

```bash
pip install -e ".[dev]"
pytest -v
```

## Dicas para uso com IA

O arquivo gerado com `--merge` é ideal para:

- **Resumos**: Envie o `_CURSO_COMPLETO.txt` para o Claude e peça um resumo por seção
- **Flashcards**: Peça para extrair conceitos-chave em formato de perguntas e respostas
- **Busca**: Use `grep` ou qualquer editor para buscar tópicos específicos
- **Ollama local**: Processe com modelos locais no seu homelab

## Notas

- Só funciona com cursos **que você comprou**
- Depende das legendas/captions que o instrutor disponibilizou
- Nem todas as aulas possuem transcrição
- Respeite os termos de uso da Udemy (uso pessoal)