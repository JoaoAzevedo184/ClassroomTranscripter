# 📝 Formato Obsidian

O `ObsidianFormatter` gera notas `.md` otimizadas pra estudo, e funciona pra
qualquer plataforma — o frontmatter e as tags refletem dinamicamente a origem
(`platform: udemy` vs `platform: dio` vs `platform: alura`).

## Saída do download

- **Frontmatter YAML dinâmico** — `course`, `section`, `tags`, `date`,
  `platform` (funciona com Dataview)
- **Tags automáticas** — `#udemy`/`#dio`/`#alura`, `#curso/nome`, `#secao/nome`
- **Navegação** — wikilinks `⬅ [[anterior]] | [[próxima]] ➡` (callout `[!tip]`)
- **MOC (Map of Content)** — `_MOC.md` com links pra todas as notas
- **Índice por seção** — `_index.md` com lista numerada de aulas
- **Área de anotações** — espaço reservado pra notas pessoais

---

## Estrutura de saída

```
udemy_transcripts/
└── Docker Zero a Profissional/
    ├── _MOC.md                     # Map of Content
    ├── _CURSO_COMPLETO.md          # (com --merge)
    ├── _metadata.json
    ├── 01 - Primeiros Passos/
    │   ├── _index.md               # Índice da seção
    │   ├── 014 - Instalando o Docker.md
    │   └── 015 - O que sao Containers.md
    └── 02 - Construindo Imagens/
        ├── _index.md
        ├── 027 - Entendendo Layers.md
        └── 028 - Criando seu primeiro Dockerfile.md
```

DIO e Alura geram a mesma estrutura, mas em `dio_transcripts/` e
`alura_transcripts/`.

---

## Frontmatter dinâmico por plataforma

```yaml
# Aula da Udemy
---
course: "Docker Zero a Profissional"
section: "Primeiros Passos"
lecture: 14
udemy_id: 12345678
platform: udemy
date: 2026-05-21
tags:
  - udemy
  - curso/docker-zero-a-profissional
  - secao/primeiros-passos
---

# Aula da DIO
---
course: "Jornada Node"
section: "Fundamentos"
lecture: 1
dio_id: 01-introducao.mp4
platform: dio
date: 2026-05-21
tags:
  - dio
  - curso/jornada-node
  - secao/fundamentos
---
```

A chave `{platform}_id` é dinâmica — facilita queries no Dataview filtradas por
plataforma.

---

## Estilo após enriquecimento

Após rodar `classroom-enrich`, as notas viram material didático visual:
headings com emojis, seções escaneáveis, blocos de código, callouts e perguntas
de revisão.

### Elementos visuais

| Elemento | Descrição |
|----------|-----------|
| `# 📚 Visão Geral da Aula` | Resumo do tema em 1-2 parágrafos |
| `# 🎯 Objetivos` | O que o aluno vai aprender |
| `# 🧠 Conceitos` | Conteúdo principal por tópicos |
| `# 👨‍🏫 Sobre o Instrutor` | Se a aula apresentar alguém |
| `# 🧾 Resumo da Aula` | 3-5 bullets com lições principais |
| `# 🔁 Perguntas para Revisão` | 3-5 perguntas pra fixação |
| `# ✍️ Anotações` | Espaço vazio pro aluno |

### Callouts do Obsidian

```markdown
> [!tip] Dica prática
> Use Docker Compose pra orquestrar múltiplos containers.

> [!warning] Atenção
> Não esqueça do .dockerignore pra evitar enviar node_modules.

> [!info] Importante
> Containers compartilham o kernel do host, diferente de VMs.

> [!example] Exemplo
> Uma app com backend, banco e cache como 3 serviços no Compose.
```

### Separadores e escaneabilidade

- `---` entre todas as seções principais
- Blocos curtos de 5-8 linhas (sem paredes de texto)
- Um conceito por subseção `###`
- Bullets curtos com termos em **negrito**
- ✅/❌ pra indicar foco vs fora do escopo

---

## Exemplo: antes e depois

### Antes (transcrição bruta)

```markdown
## Transcrição

Muito bem vindo ao curso de Docker de zero a profissional pra
desenvolvimento web. Este curso é o curso que te vai levar
definitivamente ao conhecimento do uso desta tecnologia enquanto
programador, mas obviamente contém muitos conteúdos que te poderão
preparar pra um outro tipo de funções, como é o caso de DevOps...
```

### Depois (enriquecido)

```markdown
---

# 📚 Visão Geral da Aula

Esta aula apresenta o **objetivo do curso**, o **perfil do instrutor**
e explica **o que será aprendido ao longo do treinamento**.

O foco do curso é ensinar **Docker pra desenvolvedores web**,
principalmente pra criar **ambientes de desenvolvimento local**.

---

# 🎯 Objetivos do Curso

Ao final do curso você será capaz de:

- Entender **o que é Docker e suas vantagens**
- Instalar Docker em Windows, Mac e Linux
- Trabalhar com **comandos básicos da CLI**
- Criar e utilizar **Dockerfiles**
- Gerenciar Images, Containers, Volumes e Networks
- Orquestrar ambientes com **Docker Compose**

---

# ⚙️ Foco do Curso

✅ Uso do Docker **no ambiente local**
✅ **Desenvolvimento web**
✅ **Aprendizado prático**

❌ Deploy em cloud
❌ Infraestrutura em AWS/Azure

---

# 🧾 Resumo da Aula

- Docker será ensinado **do zero ao nível profissional**
- O foco é **desenvolvimento web**
- O curso é **prático e conceitual**
- Pode servir de base pra evoluir pra **DevOps**

---

# 🔁 Perguntas para Revisão

1. Qual é o principal objetivo do curso?
2. O que são **Docker Images**?
3. Pra que serve o **Docker Compose**?

---

# ✍️ Anotações

> [!note] Espaço para suas anotações
>
> -
> -
> -
```

---

## Dicas pro Obsidian

### Plugins recomendados

- **Dataview** — queries no frontmatter (`course`, `tags`, `section`, `platform`)
- **Templater** — templates de anotações
- **Outline** — navegação pelos headings com emojis

### Query Dataview — todas as aulas de Docker

```dataview
TABLE platform, section, lecture
FROM #curso/docker-zero-a-profissional
SORT lecture ASC
```

### Query Dataview — todas as aulas da DIO

```dataview
TABLE course, section
FROM ""
WHERE platform = "dio"
SORT course, section
```

### Query Dataview — comparativo de plataformas

```dataview
TABLE length(rows) AS aulas
FROM ""
WHERE platform != null
GROUP BY platform
```