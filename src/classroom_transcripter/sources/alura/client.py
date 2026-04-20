"""Cliente HTTP da Alura com autenticação por sessão.

IMPLEMENTAÇÃO (Fase 7):
----------------------
A Alura usa login por email/senha que retorna cookies de sessão.
Estratégia recomendada:
1. POST /login com credenciais
2. Guarda cookies (httpx.Client com persistência)
3. Reutiliza a mesma sessão pras chamadas subsequentes

Libs: httpx (já no pyproject). curl-cffi só se tiver Cloudflare.

Funções esperadas:
- class AluraClient:
    - login(email, password) -> None
    - get_course(course_id) -> dict  (retorno da API)
    - get_transcript(course_id, lesson_id) -> str  (markdown ou HTML cru)

OBS: API da Alura não é pública. Vai precisar inspecionar as requests
do navegador logado (DevTools → Network) pra mapear os endpoints.
Alternativa: scraping com BeautifulSoup das páginas HTML.
"""
# TODO Fase 7: implementar após inspecionar API/páginas da Alura
