"""Cliente HTTP da Alura.

STATUS: esqueleto com 3 TODOs marcados. Antes de usar, você precisa inspecionar
a API real da Alura (DevTools → Network logado) e preencher os TODOs.

Guia passo-a-passo: `docs/sources/alura.md`.

Por que não veio pronto: a Alura não tem API pública documentada, então os
endpoints reais precisam ser descobertos no tráfego do navegador. Fazer isso
"no chute" produziria código que parece funcionar mas falha em runtime.
"""
from __future__ import annotations

import httpx

from classroom_transcripter.core.exceptions import (
    AuthenticationError,
    CourseNotFoundError,
    NetworkError,
    TranscriptNotAvailableError,
)


# ─── Constantes ────────────────────────────────────────────────────────────

BASE_URL = "https://cursos.alura.com.br"

# Headers mínimos pra não ser bloqueado como "bot"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


class AluraClient:
    """Cliente HTTP pra Alura, autenticado via email+senha.

    Uso:
        client = AluraClient("email@dominio.com", "senha")
        client.login()                        # popula cookies de sessão
        course_data = client.get_course("slug-do-curso")
        transcript = client.get_transcript(course_id, lesson_id)
    """

    def __init__(self, email: str, password: str, *, debug: bool = False):
        self.email = email
        self.password = password
        self.debug = debug

        # httpx.Client persiste cookies entre requests — essencial pra sessão
        self.session = httpx.Client(
            base_url=BASE_URL,
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0,
        )
        self._logged_in = False

    # ═════════════════════════════════════════════════════════════════════
    # TODO FASE 7.1 — LOGIN
    # ═════════════════════════════════════════════════════════════════════
    def login(self) -> None:
        """Autentica na Alura e guarda cookies de sessão.

        COMO PREENCHER (inspeção no DevTools):
        --------------------------------------
        1. Abra `https://cursos.alura.com.br/loginForm` em aba anônima
        2. DevTools (F12) → aba Network → filtrar "Fetch/XHR" + "Doc"
        3. Faça login normalmente
        4. Procure a requisição de POST do formulário — provavelmente
           `POST /auth/login` ou `POST /loginForm` ou similar
        5. Anote:
            a) URL exata do endpoint
            b) Content-Type (application/x-www-form-urlencoded ou application/json)
            c) Campos do body (username/email, password, csrf_token?)
            d) Se há CSRF token: GET inicial pra pegá-lo

        IMPLEMENTAÇÃO EXEMPLO (ajuste os detalhes):
        ```python
        # Se tiver CSRF token:
        initial = self.session.get("/loginForm")
        # BeautifulSoup pra extrair <input name="_csrf" value="...">
        # csrf = ...

        response = self.session.post(
            "/auth/login",  # ← URL REAL descoberta no DevTools
            data={           # ← ou json={...} se for JSON
                "username": self.email,
                "password": self.password,
                # "_csrf": csrf,  # se precisar
            },
        )

        # Valide: login ok costuma retornar 200 ou 302 com cookie de sessão
        if response.status_code >= 400 or "loginForm" in str(response.url):
            raise AuthenticationError(
                "Login falhou. Email/senha inválidos ou a API mudou."
            )

        self._logged_in = True
        ```
        """
        raise NotImplementedError(
            "TODO Fase 7.1: preencher AluraClient.login() "
            "seguindo docs/sources/alura.md §1"
        )

    # ═════════════════════════════════════════════════════════════════════
    # TODO FASE 7.2 — CURRICULUM DO CURSO
    # ═════════════════════════════════════════════════════════════════════
    def get_course(self, slug: str) -> dict:
        """Retorna a estrutura bruta do curso (seções + aulas).

        COMO PREENCHER:
        ---------------
        1. Logado, acesse `https://cursos.alura.com.br/course/<slug>`
        2. DevTools → Network → Fetch/XHR
        3. Procure a request que carrega a lista de aulas. Pode ser:
            - Uma API JSON (ex: `/api/courses/{slug}/curriculum`) ← ideal
            - O próprio HTML da página com o curriculum inline em JS ← scraping
        4. Se for JSON: copie URL e estrutura da resposta
        5. Se for HTML: identifique os seletores BeautifulSoup

        Retorno esperado: dict com pelo menos:
            {
                "id": "uuid-ou-int",
                "title": "Nome do Curso",
                "sections": [
                    {
                        "id": "...",
                        "title": "Nome da Seção",
                        "index": 1,
                        "activities": [
                            {"id": "...", "title": "...", "index": 1, "type": "video"},
                            ...
                        ]
                    }
                ]
            }
        A estrutura dos dicts NÃO precisa bater com models.Course —
        o parser.py é quem faz a tradução.

        IMPLEMENTAÇÃO EXEMPLO (caso JSON):
        ```python
        if not self._logged_in:
            raise AuthenticationError("Chame login() antes.")

        response = self.session.get(f"/api/courses/{slug}/curriculum")
        if response.status_code == 404:
            raise CourseNotFoundError(f"Curso '{slug}' não encontrado.")
        if response.status_code >= 400:
            raise NetworkError(f"HTTP {response.status_code}: {response.text[:200]}")

        return response.json()
        ```
        """
        raise NotImplementedError(
            "TODO Fase 7.2: preencher AluraClient.get_course() "
            "seguindo docs/sources/alura.md §2"
        )

    # ═════════════════════════════════════════════════════════════════════
    # TODO FASE 7.3 — TRANSCRIPT DE UMA AULA
    # ═════════════════════════════════════════════════════════════════════
    def get_transcript(self, course_slug: str, activity_id: str | int) -> dict:
        """Retorna a transcrição de uma aula específica.

        COMO PREENCHER:
        ---------------
        1. Logado, abra uma aula qualquer do curso
        2. Clique na aba "Transcrição" (ou equivalente)
        3. DevTools → Network → procure a requisição. Três possibilidades:

        FORMATO A — JSON estruturado (ideal):
            {"transcript": "texto corrido...", "language": "pt"}
            ou
            {"segments": [{"start": 0, "end": 2.5, "text": "..."}]}

        FORMATO B — VTT (WebVTT puro):
            O endpoint serve um .vtt direto → parser.py chama `vtt_to_transcript`

        FORMATO C — HTML embedado na página da aula:
            Nenhuma request dedicada — a transcrição vem no HTML inicial

        Retorno esperado: dict com o formato bruto que get_transcript recebeu.
        O parser.py é quem decide como converter:
            - Se tem "segments" → constrói Transcript com cues
            - Se só tem "text"/"transcript" → constrói com plain_text
            - Se é VTT → chama core.vtt.vtt_to_transcript

        IMPLEMENTAÇÃO EXEMPLO (formato A):
        ```python
        if not self._logged_in:
            raise AuthenticationError("Chame login() antes.")

        response = self.session.get(
            f"/api/courses/{course_slug}/activities/{activity_id}/transcript"
        )
        if response.status_code == 404:
            raise TranscriptNotAvailableError(
                f"Aula {activity_id} não tem transcrição disponível."
            )
        if response.status_code >= 400:
            raise NetworkError(f"HTTP {response.status_code}")

        # Se for VTT puro:
        # return {"format": "vtt", "content": response.text}
        # Se for JSON:
        return response.json()
        ```
        """
        raise NotImplementedError(
            "TODO Fase 7.3: preencher AluraClient.get_transcript() "
            "seguindo docs/sources/alura.md §3"
        )

    # ─── Utilitários ──────────────────────────────────────────────────

    def close(self) -> None:
        """Fecha a sessão HTTP. Chame ao terminar (ou use como context manager)."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
