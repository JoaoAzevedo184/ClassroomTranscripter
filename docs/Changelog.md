# Changelog

Todas as mudanças notáveis deste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [1.1.0] — 2026-04-20

### Adicionado
- **`platforms.py`** — abstração `BasePlatform` com `UdemyPlatform` como implementação padrão. Prepara o projeto para suporte futuro a Alura, DIO e outras plataformas
- **`--resume` / `-r`** — nova flag de download para retomar sessões interrompidas. Aulas já baixadas são puladas automaticamente; conteúdo existente é carregado para geração do merge
- **`.env.example`** — arquivo de exemplo de configuração com documentação inline de todas as variáveis suportadas (`UDEMY_COOKIES`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `LANG_PRIORITY`, `OLLAMA_URL`)
- **`LANG_PRIORITY` configurável via `.env`** — agora é possível definir `LANG_PRIORITY=pt,en,es` no `.env` sem alterar o código. Compatibilidade total com imports existentes mantida
- `get_lang_priority()` em `config.py` — função pública para leitura dinâmica da prioridade de idiomas
- `detect_platform(url)` e `get_platform(name)` em `platforms.py` — detecção automática e lookup por nome de plataforma
- Entrypoint `classroom-transcripter` no `pyproject.toml` (alias legado `udemy-transcripter` mantido)
- URLs do projeto (`Homepage`, `Repository`, `Issues`) no `pyproject.toml`
- Classifiers e keywords no `pyproject.toml` para melhor indexação no PyPI

### Corrigido
- `ClaudeProvider` — model string atualizado de `claude-sonnet-4-20250514` para `claude-sonnet-4-6`
- `Requirements.txt` — removida dependência `google-generativeai` que não era usada (provider Gemini usa API OpenAI-compatible via `requests`)
- `formatters.py` — `import re` movido para o topo do arquivo; eliminados dois imports dentro de funções (`_slugify_tag` e `_split_into_paragraphs`)
- `downloader.py` — relatório final passa a exibir aulas puladas (`--resume`) separadamente das baixadas

### Alterado
- `LLMProvider` — adicionado método base `_post_with_retry()` que centraliza a lógica de retry (HTTP 429) antes duplicada entre `GroqProvider` e `GeminiProvider`
- `utils.extract_slug()` — delegado para `UdemyPlatform.extract_slug()` mantendo compatibilidade total com a assinatura anterior
- `__init__.py` — exporta `BasePlatform`, `UdemyPlatform`, `get_platform`, `detect_platform`
- `pyproject.toml` — nome do pacote atualizado de `udemy-transcripter` para `classroom-transcripter`; versão bump `1.0.0` → `1.1.0`
- Comentários em `downloader.py` explicam explicitamente a escolha de dois clientes HTTP (`curl_cffi` para API Udemy, `requests` para VTTs em CDN)

---

## [1.0.0] — 2026-04-19

### Adicionado
- Download de transcrições da Udemy via API interna
- Bypass de Cloudflare usando `curl_cffi` com fingerprint Chrome
- Formatadores `txt` (texto simples) e `obsidian` (Markdown com frontmatter YAML, wikilinks e MOC)
- Enriquecimento com IA via Ollama, Groq, Gemini e Claude
- `--merge` para gerar arquivo único com todo o curso
- `--timestamps` para incluir marcações de tempo
- `--list-langs` para listar idiomas disponíveis
- `--setup` para configuração interativa do `.env`
- `--dry-run` para preview do enriquecimento sem salvar
- 69 testes unitários