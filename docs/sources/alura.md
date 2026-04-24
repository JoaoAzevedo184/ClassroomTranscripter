# Alura

> **Status:** Fase 7 entregue como esqueleto. Pra ativar, preencha os 3 TODOs em `src/classroom_transcripter/sources/alura/client.py` seguindo este guia.

A Alura não expõe API pública documentada, então os endpoints precisam ser descobertos no tráfego do navegador. O esqueleto está 90% pronto — só falta o cliente HTTP saber qual URL chamar e com qual payload.

## O que já funciona

- `AluraSource(TranscriptSource)` completo — só delega pro client + parser
- `parser.py` implementado, suporta 3 formatos de resposta (JSON segments, JSON texto, VTT)
- `cli/alura_cli.py` completo com `--email`, `--password`, `--ask-password`, `.env`, todas as flags de download
- 27 testes passando com mocks

## O que falta preencher

Só 3 métodos em `src/classroom_transcripter/sources/alura/client.py`:

1. **`login()`** — autenticar na Alura
2. **`get_course(slug)`** — buscar curriculum do curso
3. **`get_transcript(course_slug, activity_id)`** — buscar transcrição de uma aula

Cada método tem docstring detalhada com exemplo de implementação.

## §1 — Descobrindo o endpoint de login

### Passos

1. Abra uma aba **anônima** do navegador (sem sessão ativa)
2. Vá em `https://cursos.alura.com.br/loginForm`
3. Abra **DevTools** (F12) → aba **Network**
4. Filtros: ative "Fetch/XHR" + "Doc" (pra pegar também form submits clássicos)
5. Ative "Preserve log" (o redirect não pode apagar o histórico)
6. Faça login normalmente

### O que anotar

Procure a requisição que **POSTa** com seus credenciais. Anote:

| Item | Exemplo (preencha com o real) |
|---|---|
| URL | `POST /auth/login` ou `POST /loginForm` |
| Content-Type | `application/x-www-form-urlencoded` ou `application/json` |
| Payload | Campos do body: `username`, `password`, `_csrf`, etc. |
| Status esperado | Geralmente 200 ou 302 com cookie de sessão |
| Nome do cookie | Geralmente `JSESSIONID`, `ALURA_SESSION`, etc. |

### Se houver CSRF token

Algumas páginas exigem token CSRF anti-forgery. Verificação:
- Faça um GET em `/loginForm` e inspecione o HTML da resposta
- Se houver `<input type="hidden" name="_csrf" value="...">`, é CSRF
- Nesse caso, o fluxo vira: GET `/loginForm` → extrai token → POST com token

### Implementação

Substitua o `raise NotImplementedError` do método `login()` pela lógica real. Exemplo quando a Alura usa form-encoded sem CSRF:

```python
def login(self) -> None:
    response = self.session.post(
        "/auth/login",  # ← URL REAL
        data={
            "username": self.email,  # ← nome real do campo
            "password": self.password,
        },
    )

    # Login bem-sucedido tipicamente redireciona pra /home ou dashboard.
    # Login falho devolve 200 com a mesma tela de login.
    if response.status_code >= 400 or "loginForm" in str(response.url):
        raise AuthenticationError(
            "Login falhou. Email/senha inválidos ou a API mudou."
        )

    self._logged_in = True
```

## §2 — Descobrindo o endpoint de curriculum

### Passos

1. Logado, abra a página de algum curso: `https://cursos.alura.com.br/course/<slug>`
2. DevTools → Network → Fetch/XHR
3. Recarregue a página (Ctrl+R)
4. Procure a request que traz a **lista de seções e aulas**

### Dois casos

**Caso A — existe API JSON dedicada** (ideal):
- URL tipo `/api/courses/{slug}/curriculum` ou `/course/{slug}/sections`
- Retorno em JSON estruturado

**Caso B — o HTML da página já tem tudo inline** (mais comum em sites antigos):
- A página HTML contém `<script>window.course = {...}</script>` ou similar
- Ou os DOM elements com a lista precisam ser scrapeados com BeautifulSoup

### Implementação — Caso A (JSON)

```python
def get_course(self, slug: str) -> dict:
    if not self._logged_in:
        raise AuthenticationError("Chame login() antes.")

    response = self.session.get(f"/api/courses/{slug}/curriculum")
    if response.status_code == 404:
        raise CourseNotFoundError(f"Curso '{slug}' não encontrado.")
    if response.status_code >= 400:
        raise NetworkError(f"HTTP {response.status_code}: {response.text[:200]}")

    raw = response.json()
    # IMPORTANTE: o parser.py espera formato padronizado. Se a Alura retornar
    # shape diferente, adapte AQUI (ex: renomear chaves) antes de retornar.
    return raw
```

### Implementação — Caso B (scraping HTML)

```python
def get_course(self, slug: str) -> dict:
    if not self._logged_in:
        raise AuthenticationError("Chame login() antes.")

    from bs4 import BeautifulSoup

    response = self.session.get(f"/course/{slug}")
    if response.status_code >= 400:
        raise CourseNotFoundError(f"Curso '{slug}' não acessível.")

    soup = BeautifulSoup(response.text, "html.parser")

    # Mapeie os seletores REAIS aqui (use DevTools → Inspect Element)
    sections = []
    for idx, section_el in enumerate(soup.select(".section-card"), start=1):
        title = section_el.select_one(".section-title").get_text(strip=True)
        activities = []
        for a_idx, a_el in enumerate(section_el.select(".activity-item"), start=1):
            activities.append({
                "id": a_el.get("data-activity-id"),
                "title": a_el.select_one(".title").get_text(strip=True),
                "index": a_idx,
                "type": a_el.get("data-type", "video"),
            })
        sections.append({
            "title": title, "index": idx, "activities": activities,
        })

    return {
        "id": slug, "title": soup.select_one("h1.course-title").get_text(strip=True),
        "sections": sections,
    }
```

## §3 — Descobrindo o endpoint de transcript

### Passos

1. Logado, abra uma aula qualquer
2. Clique na aba "**Transcrição**" (ou equivalente)
3. DevTools → Network → Fetch/XHR
4. Anote o que aparece

### Três formatos possíveis

O `parser.py` já sabe lidar com os 3 — você só precisa descobrir qual é:

**Formato A — JSON com segments** (melhor caso):
```json
{
  "language": "pt",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Olá"},
    {"start": 2.5, "end": 5.0, "text": "bem-vindos"}
  ]
}
```

**Formato B — JSON com texto corrido**:
```json
{"language": "pt", "transcript": "Olá, bem-vindos ao curso..."}
```

**Formato C — VTT direto**:
O endpoint devolve `Content-Type: text/vtt` com conteúdo `WEBVTT\n\n...`.

### Implementação

```python
def get_transcript(self, course_slug: str, activity_id: str | int) -> dict:
    if not self._logged_in:
        raise AuthenticationError("Chame login() antes.")

    response = self.session.get(
        f"/api/courses/{course_slug}/activities/{activity_id}/transcript"
    )
    if response.status_code == 404:
        raise TranscriptNotAvailableError(
            f"Aula {activity_id} não tem transcrição."
        )
    if response.status_code >= 400:
        raise NetworkError(f"HTTP {response.status_code}")

    # Se for VTT direto:
    if "text/vtt" in response.headers.get("content-type", ""):
        return {"format": "vtt", "content": response.text}

    # Senão, JSON (formato A ou B — parser.py trata os dois):
    return response.json()
```

## Ajuste no parser se necessário

O `parse_course()` atual popula `lecture.metadata` com `type` e `module_index`, mas o `fetch_transcript()` precisa do `course_slug` da aula. Se a API da Alura não mandar isso junto, ajuste `_parse_lecture` em `parser.py`:

```python
def _parse_lecture(activity: dict, module_index: int, course_slug: str = "") -> Lecture:
    return Lecture(
        id=activity["id"],
        title=activity.get("title", "Sem título"),
        object_index=activity.get("index", 0),
        metadata={
            "type": activity.get("type", "video"),
            "module_index": module_index,
            "course_slug": course_slug,  # ← ADICIONAR
        },
    )
```

E atualize `parse_course` pra passar o `slug`:

```python
def parse_course(raw: dict, slug: str) -> Course:
    modules = [
        _parse_module(section, course_slug=slug)  # ← passar
        for section in raw.get("sections", [])
    ]
    # ...
```

## Configuração

Crie/atualize `.env`:

```bash
ALURA_EMAIL=seu@email.com
ALURA_PASSWORD='sua-senha-com-caracteres-especiais-entre-aspas'
```

## Teste final

Depois de preencher os 3 TODOs:

```bash
# Checa se os testes ainda passam (eles são isolados por mocks, nada deveria quebrar)
pytest tests/sources/alura/ -v

# Teste real (ele vai falhar cedo se algum endpoint tiver errado)
classroom-alura --url "https://cursos.alura.com.br/course/docker-fundamentos" \
  --format obsidian --debug

# Se funcionar, sem o --debug
classroom-alura --url "..." --merge
```

## Debug

Se der erro tipo "login falhou" mesmo com credenciais corretas:
- Abra o `.debug` e olhe se o POST tá indo pra URL certa
- Confira se os nomes dos campos batem (`username` vs `email` vs `login`)
- Verifique se há um token CSRF que você não tá enviando

Se der erro tipo "curso não encontrado":
- O slug da URL pode ser diferente do slug que a API espera
- Tente logar no site e copiar o slug da URL depois do login

Se as transcrições vierem vazias:
- O endpoint pode estar certo mas a Alura marcar o curso como sem transcrição
- Teste manualmente se a aba "Transcrição" aparece no site

## Quando ativar

Você pode usar `classroom-udemy` e `classroom-dio` normalmente enquanto deixa a Alura pra depois. O CLI `classroom-alura` vai dar uma mensagem amigável enquanto os TODOs não forem preenchidos.
