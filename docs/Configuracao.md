# ⚙️ Configuração

O projeto usa um arquivo `.env` na raiz pra armazenar credenciais e
preferências.

```bash
# Setup interativo dos cookies da Udemy (recomendado pra começar)
classroom-setup
# ou
classroom udemy --setup

# Ou copie o template e preencha manualmente
cp .env.example .env
```

> 💡 Só preencha as variáveis das plataformas/providers que você vai usar. Não
> precisa configurar Alura se só vai mexer com Udemy, por exemplo.

---

## Udemy — cookies do navegador

Necessário pro `classroom-udemy`. Os cookies autenticam suas requisições à API
interna da Udemy.

**Como obter:**

1. Acesse [udemy.com](https://udemy.com) e faça login
2. Abra o **DevTools** (`F12`) → aba **Network**
3. Recarregue a página de qualquer curso
4. Clique em alguma requisição pra `www.udemy.com`
5. Em **Request Headers**, copie o valor completo do header **`Cookie`**

**No `.env`:**

```env
UDEMY_COOKIES='access_token=xxx; cf_clearance=yyy; client_id=zzz; ...'
```

> ⚠️ Nunca compartilhe seus cookies. Eles dão acesso à sua conta. Cookies
> expiram periodicamente — se der erro 403, gere novos com `classroom-setup`.

---

## DIO — pasta de vídeos e Whisper

Necessário pro `classroom-dio`. A DIO não tem API pública, então você precisa
baixar os `.mp4` manualmente e organizar em subpastas por módulo. Veja
[`docs/sources/dio.md`](sources/dio.md) pra detalhes.

**No `.env`:**

```env
# Pasta raiz padrão (pode ser sobrescrito por --video-dir)
DIO_VIDEO_DIR=./dio_videos

# Modelo Whisper: tiny | base | small | medium | large
WHISPER_MODEL=small

# Idioma falado nas aulas (código ISO)
WHISPER_LANGUAGE=pt
```

**Instalação:**

DIO precisa de Whisper + ffmpeg. Instale o extra `[dio]`:

```bash
pip install 'classroom-transcripter[dio]'

# E o ffmpeg do sistema (não vem com pip)
sudo apt install ffmpeg          # Ubuntu/Pop!_OS/Debian
sudo dnf install ffmpeg          # Fedora
brew install ffmpeg              # macOS
```

**Modelos Whisper — qualidade vs velocidade:**

| Modelo | Tamanho | RAM | Velocidade | Uso |
|--------|:---:|:---:|:---:|---|
| tiny | ~75MB | ~1GB | Muito rápida | Testes |
| base | ~140MB | ~1GB | Rápida | Aulas curtas |
| **small** | ~460MB | ~2GB | Boa | **Padrão recomendado** |
| medium | ~1.5GB | ~5GB | Lenta | Qualidade alta |
| large | ~3GB | ~10GB | Muito lenta | Máxima qualidade |

---

## Alura — email e senha

Necessário pro `classroom-alura`. Veja [`docs/sources/alura.md`](sources/alura.md)
pro estado atual (esqueleto ativável — 3 funções precisam ser preenchidas
após inspeção do DevTools).

**No `.env`:**

```env
ALURA_EMAIL=seu@email.com
ALURA_PASSWORD='sua-senha-aqui'
```

> 💡 Use aspas simples na senha se ela tiver caracteres especiais (`!`, `$`, `"`).
> Alternativa: passe `--ask-password` no CLI pra digitar interativamente sem
> deixar a senha no histórico do shell.

---

## Groq — gratuito, ultra-rápido (recomendado)

Necessário pro `classroom-enrich --provider groq`. Rodando os mesmos modelos
open source (Llama, DeepSeek) em LPUs ultra-rápidas.

**Como obter:**

1. Acesse [console.groq.com](https://console.groq.com)
2. Crie conta (Google, sem cartão de crédito)
3. **API Keys** → **Create API Key**
4. Copie a chave (começa com `gsk_`)

**No `.env`:**

```env
GROQ_API_KEY=gsk_sua_chave_aqui
```

**Modelos disponíveis:**

| Modelo | Tokens/min | Tokens/dia | Uso |
|--------|:---:|:---:|---|
| `llama-3.3-70b-versatile` (padrão) | ~6.000 | ~500.000 | Melhor qualidade |
| `llama-3.1-8b-instant` | ~30.000 | maior | Mais rápido |
| `deepseek-r1-distill-llama-70b` | ~6.000 | ~500.000 | Raciocínio/código |

**Rate limits:** Os limites resetam diariamente. Se atingir, espere até o dia
seguinte e rode o mesmo comando — arquivos já enriquecidos são pulados
automaticamente. O enricher também retenta automaticamente em 429.

**Dicas pra cursos longos (100+ aulas):**

- Use `--delay 5` pra espaçar chamadas
- Use `--model llama-3.1-8b-instant` (limites mais altos)
- Combine providers: parte com Groq, parte com Gemini

---

## Google Gemini — gratuito (alternativa ao Groq)

**Como obter:**

1. Acesse [aistudio.google.com](https://aistudio.google.com)
2. Faça login com conta Google
3. **Get API Key** → **Create API Key**
4. Copie a chave (começa com `AIzaSy`)

**No `.env`:**

```env
GEMINI_API_KEY=AIzaSy_sua_chave_aqui
```

**Modelos disponíveis:**

| Modelo | RPM | RPD | Uso |
|--------|:---:|:---:|---|
| `gemini-2.5-flash` (padrão) | 10 | 500 | Equilíbrio |
| `gemini-2.5-pro` | 5 | 100 | Máxima qualidade |
| `gemini-2.5-flash-lite` | 15 | 1.000 | Volume alto |

Rate limits resetam à meia-noite (Pacífico). Mesma lógica do Groq.

---

## Ollama — local, ilimitado

Roda no seu próprio hardware. Sem limites, sem internet, sem custos.

```bash
# Instalar modelo (uma vez)
ollama pull llama3.1            # 8B, ~5GB
ollama pull qwen2.5:14b         # 14B, ~9GB (recomendado pra qualidade)
ollama pull qwen2.5-coder:7b    # 7B, melhor pra código
```

Não precisa de API key. O enricher se conecta automaticamente em
`http://localhost:11434`.

**Ollama em outra máquina da rede (ex: homelab):**

```bash
classroom-enrich ./transcripts/X --provider ollama \
  --ollama-url http://192.168.1.100:11434
```

**No `.env`:**

```env
OLLAMA_URL=http://localhost:11434
```

**Requisitos de hardware:**

| Modelo | RAM mínima |
|--------|:---:|
| Llama 3.1 8B (Q4) | ~8 GB |
| Qwen 2.5 14B (Q4) | ~12 GB |
| Qwen 2.5 32B (Q4) | ~24 GB |

---

## Claude (Anthropic) — pago, melhor qualidade

Necessário pro `classroom-enrich --provider claude`. Requer créditos pagos.

**Como obter:**

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Crie uma conta ou faça login
3. **Settings** → **API Keys** → **Create Key**
4. Copie a chave (começa com `sk-ant-`)
5. Adicione créditos em **Plans & Billing** (mínimo $5)

**No `.env`:**

```env
ANTHROPIC_API_KEY=sk-ant-api03-sua-chave-aqui
```

**Modelo padrão:** `claude-sonnet-4-6` (rápido, alta qualidade).

Custo estimado pra ~100 aulas: **$0.50 – $2.00** com Sonnet.

**Ordem de resolução da API key:**

1. Flag `--api-key` na CLI
2. Variável no `.env`
3. Variável de ambiente do sistema

---

## Variáveis adicionais

```env
# Prioridade de idiomas pras legendas (Udemy/Alura)
# Default: pt,pt-BR,en,en_US,en_GB,es
LANG_PRIORITY=pt,en,es
```

---

## Resumo dos providers

| Provider | Custo | Velocidade | Qualidade | Variável `.env` |
|----------|:---:|:---:|:---:|---|
| **Groq** | Gratuito | Ultra-rápido | Alta | `GROQ_API_KEY` |
| **Gemini** | Gratuito | Rápido | Alta | `GEMINI_API_KEY` |
| **Ollama** | Gratuito | Local (variável) | Boa | Não precisa |
| **Claude** | Pago | Rápido | Excelente | `ANTHROPIC_API_KEY` |