# ❓ FAQ e Troubleshooting

## Geral

### O projeto é gratuito?

Sim. Download e transcrição (Udemy, DIO, Alura) são gratuitos. Enriquecimento
com Groq, Gemini ou Ollama também. Apenas o Claude requer créditos pagos.

### Funciona com qualquer curso?

- **Udemy/Alura:** só funciona com cursos **que você comprou** e que tenham
  legendas/captions habilitadas pelo instrutor
- **DIO:** funciona com qualquer bootcamp que você tenha baixado em `.mp4` —
  como usa Whisper local, não depende de legendas oficiais

### Quais plataformas estão prontas?

- ✅ **Udemy** — 100% funcional desde a v0.1
- ✅ **DIO** — 100% funcional via Whisper local
- 🟡 **Alura** — esqueleto ativável. Veja [`docs/sources/alura.md`](sources/alura.md)
  pra preencher os 3 TODOs após inspeção do DevTools

---

## Erros de download (Udemy)

### Erro 403 / "Just a moment..."

Proteção **Cloudflare**. Causas:

1. **Cookies expirados** — gere novos com `classroom-setup`
2. **Curso não comprado** — verifique se você tem acesso ao curso
3. **Cookies incompletos** — copie o header `Cookie` **inteiro** do DevTools

```bash
# Sempre rode com --debug pra ver detalhes
classroom-udemy --url "..." --list-langs --debug
```

### Erro 401

Token inválido ou expirado. Gere novos cookies:

```bash
classroom-setup
```

### Por que tem aulas faltando na numeração?

O `object_index` (001, 002, 015...) é a numeração interna da plataforma que
conta **todos** os itens do curso. O script pula itens sem legenda: quizzes,
exercícios práticos, artigos e vídeos sem caption.

### "Nenhuma legenda disponível"

O curso provavelmente não tem captions habilitadas. Use `--list-langs` pra
verificar. Sem captions, não é possível extrair transcrição via Udemy/Alura.

> 💡 Alternativa: se você tem o curso no disco, pode usar `classroom-dio` (que
> usa Whisper local) mesmo que ele não seja da DIO.

---

## Erros DIO / Whisper

### "Whisper não instalado"

Instale o extra opcional:

```bash
pip install 'classroom-transcripter[dio]'
```

### "FileNotFoundError: ffmpeg"

Whisper precisa do `ffmpeg` no sistema:

```bash
sudo apt install ffmpeg          # Ubuntu/Pop!_OS/Debian
sudo dnf install ffmpeg          # Fedora
brew install ffmpeg              # macOS
```

### "Pasta não contém subpastas de módulos"

A DIO exige estrutura profunda obrigatória:

```
meu-bootcamp/
├── 01-fundamentos/
│   ├── 01-introducao.mp4
│   └── 02-variaveis.mp4
└── 02-apis/
    └── 01-rest.mp4
```

Estrutura plana (todos os `.mp4` direto na raiz) é erro proposital — força
você a organizar antes de transcrever. Veja
[`docs/sources/dio.md`](sources/dio.md) pra detalhes.

### Whisper muito lento

- Use modelo menor: `--whisper-model tiny` ou `base`
- Se você tem GPU compatível, o Whisper detecta automaticamente via PyTorch
- Pra retomar interrupções sem retranscrever tudo: use `--resume`

### "GPU out of memory"

Modelo grande demais pra placa. Diminua:

```bash
classroom-dio --video-dir ./curso --whisper-model small  # em vez de medium/large
```

---

## Erros de enriquecimento

### Groq: "Rate limit exceeded"

Limites do tier gratuito resetam **diariamente**. Não precisa pagar. Espere o
dia seguinte e rode o mesmo comando — arquivos já processados são pulados.

Pra minimizar rate limits:

- Use `--delay 5` (ou mais)
- Use `--model llama-3.1-8b-instant` (limites mais altos)
- Combine Groq + Gemini pra processar mais por dia

### Claude: "Your credit balance is too low"

A conta da Anthropic não tem créditos. Opções:

- Compre créditos em [console.anthropic.com](https://console.anthropic.com/settings/billing)
  (mínimo $5)
- Ou use **Groq** ou **Gemini** gratuitamente

### Gemini: "429 Too Many Requests"

Mesmo comportamento do Groq — limites diários. Espere o dia seguinte. O
enricher retenta automaticamente.

### Ollama: "Connection refused"

O serviço Ollama não está rodando:

```bash
# Inicie o Ollama
ollama serve

# Verifique
curl http://localhost:11434/api/tags
```

### "unrecognized arguments" com espaços no caminho

Coloque o caminho entre aspas:

```bash
# ❌ Errado
classroom-enrich ./udemy_transcripts/Docker Zero a Profissional --provider groq

# ✅ Correto
classroom-enrich "./udemy_transcripts/Docker Zero a Profissional" --provider groq
```

---

## Enriquecimento

### Posso misturar providers?

Sim. Rode metade com Groq, metade com Gemini. O marcador
`<!-- enriched-by: -->` impede reprocessamento. Pra re-enriquecer com outro
provider, delete a linha do marcador no final do arquivo.

### A qualidade do Groq é boa?

Groq roda os mesmos modelos open source (Llama 3.3 70B, DeepSeek R1) que
rodariam no Ollama — só em 3-5s em vez de 30-60s. A qualidade é do modelo, não
do provider.

### Como re-enriquecer uma aula?

Delete o marcador do final do arquivo `.md`:

```
<!-- enriched-by: groq/llama-3.3-70b-versatile -->
```

Remova essa linha e rode `classroom-enrich` novamente.

### O enricher alterou meu frontmatter!

O system prompt instrui a LLM a preservar o frontmatter, mas modelos menores
podem falhar. O código verifica e reconstrói o frontmatter original se
necessário. Se persistir, use um modelo maior (70B+).

---

## Obsidian

### Como importar as notas?

Copie a pasta do curso pra dentro do seu vault:

```bash
classroom-udemy --url "..." --format obsidian \
  --output ~/Obsidian/MeuVault/Cursos
```

Ou mova depois:

```bash
mv ./udemy_transcripts/MeuCurso ~/Obsidian/MeuVault/Cursos/
```

### As tags não aparecem no Obsidian

Verifique se o frontmatter está correto (bloco `---` no início). O Obsidian lê
tags do campo `tags:` no YAML. Reinicie o Obsidian se necessário.

### Como filtrar por plataforma no Dataview?

O frontmatter inclui `platform: udemy|dio|alura`:

```dataview
TABLE course, section
FROM ""
WHERE platform = "dio"
SORT course
```

### Plugins recomendados

- **Dataview** — queries no frontmatter (listar aulas, filtrar por plataforma)
- **Templater** — templates pra anotações
- **Outline** — navegação pelos headings com emojis

---

## Geral / Arquitetura

### Posso adicionar uma 4ª plataforma (Coursera, Rocketseat, etc)?

Sim. Implementa a ABC `TranscriptSource` em `sources/coursera/source.py`, cria
um `cli/coursera_cli.py` e registra entry point no `pyproject.toml`. Nada no
`core/` precisa mudar.

Veja [`docs/arquitetura.md`](arquitetura.md) pro racional completo.

### O projeto continua mantido?

Sim. A refatoração multi-source da v0.2.0 desbloqueia evolução por plataforma
sem mexer no núcleo compartilhado. Próximos passos vão depender de demanda da
comunidade — abra uma issue se precisar de algo.