"""`UdemySource`: implementação de `TranscriptSource` para Udemy.

Envelopa `UdemyClient` + `core.vtt.vtt_to_transcript` pra expor uma API
uniforme que conversa com o resto do pipeline (downloader, formatters,
enricher) sem depender de detalhes da Udemy.

Uso típico:
    source = UdemySource(cookie="access_token=...; ...")
    source.authenticate()
    course = source.fetch_course("https://udemy.com/course/docker-basico/")
    for lecture in course.iter_lectures():
        transcript = source.fetch_transcript(lecture)
        # ... formata/salva/enriquece
"""
from __future__ import annotations

import requests

from classroom_transcripter.core.exceptions import (
    AuthenticationError,
    CourseNotFoundError,
    ParseError,
    TranscriptNotAvailableError,
)
from classroom_transcripter.core.models import Caption, Course, Lecture, Transcript
from classroom_transcripter.core.platforms import UdemyPlatform
from classroom_transcripter.core.utils import pick_caption
from classroom_transcripter.core.vtt import vtt_to_transcript
from classroom_transcripter.sources.base import TranscriptSource
from classroom_transcripter.sources.udemy.client import UdemyClient
from classroom_transcripter.sources.udemy.parser import build_course


class UdemySource(TranscriptSource):
    """TranscriptSource para Udemy (cookies + API interna + VTT)."""

    name = "udemy"

    def __init__(
        self,
        cookie: str,
        *,
        language: str = "pt",
        debug: bool = False,
    ):
        """
        Args:
            cookie: cookie string completa do navegador (inclui access_token
                    e idealmente cf_clearance pra passar pelo Cloudflare).
            language: idioma preferido pras captions (fallback via LANG_PRIORITY).
            debug: se True, imprime detalhes das requisições HTTP.
        """
        self.cookie = cookie
        self.language = language
        self.debug = debug
        self._client: UdemyClient | None = None

    # ─── Helpers internos ──────────────────────────────────────────────

    @property
    def client(self) -> UdemyClient:
        """Cliente lazy: só instancia na primeira chamada (facilita testes)."""
        if self._client is None:
            self._client = UdemyClient(self.cookie, debug=self.debug)
        return self._client

    # ─── API do TranscriptSource ──────────────────────────────────────

    def authenticate(self) -> None:
        """Valida o cookie fazendo uma chamada leve a /users/me.

        Levanta `AuthenticationError` se o token estiver inválido/expirado.
        Implementação intencionalmente barata — não baixa curriculum nem nada.
        """
        from classroom_transcripter.core.config import UDEMY_API_BASE

        try:
            # get_course_info em um slug inválido daria 404 (não valida auth).
            # /users/me é o endpoint canônico pra checar se o token vale.
            self.client._get(f"{UDEMY_API_BASE}/users/me/")
        except AuthenticationError:
            raise
        except Exception as e:
            # Se rolar outro erro (rede, etc), propaga como falha genérica
            # — não queremos mascarar problema real como "autenticação ok".
            raise AuthenticationError(
                f"Não foi possível validar autenticação: {e}"
            ) from e

    def fetch_course(self, identifier: str) -> Course:
        """Resolve URL/slug pra um `Course` populado com módulos e aulas.

        Args:
            identifier: URL completa (`https://udemy.com/course/meu-curso/`)
                        ou slug direto (`meu-curso`).
        """
        slug = UdemyPlatform().extract_slug(identifier)

        try:
            course_id, title = self.client.get_course_info(slug)
        except Exception as e:
            # API retorna 404 como raise_for_status — vira genérico sem tipo
            raise CourseNotFoundError(
                f"Curso não encontrado ou sem acesso: {slug!r} ({e})"
            ) from e

        modules = self.client.get_curriculum(course_id)
        return build_course(
            course_id=course_id,
            title=title,
            slug=slug,
            modules=modules,
            language=self.language,
        )

    def fetch_transcript(self, lecture: Lecture) -> Transcript:
        """Escolhe a melhor caption disponível, baixa o VTT e converte em `Transcript`."""
        if not lecture.captions:
            raise TranscriptNotAvailableError(
                f"Aula {lecture.id} ({lecture.title!r}) não tem legendas disponíveis."
            )

        caption = pick_caption(lecture.captions, preferred_lang=self.language)
        if caption is None:
            raise TranscriptNotAvailableError(
                f"Nenhuma caption escolhida para aula {lecture.id}."
            )

        vtt_text = self._fetch_vtt_content(caption)
        try:
            return vtt_to_transcript(
                vtt_text,
                lecture_id=lecture.id,
                language=caption.locale,
            )
        except Exception as e:
            raise ParseError(
                f"Falha ao parsear VTT da aula {lecture.id}: {e}"
            ) from e

    # ─── Helpers específicos de Udemy ─────────────────────────────────

    def list_available_languages(self, lecture: Lecture) -> list[str]:
        """Idiomas disponíveis pras captions de uma aula (feature `--list-langs`)."""
        return [cap.locale for cap in lecture.captions]

    def _fetch_vtt_content(self, caption: Caption) -> str:
        """Baixa o conteúdo VTT de uma caption.

        Usa `requests` padrão (não curl_cffi): VTTs são servidos por CDNs sem
        proteção Cloudflare. Comentário preservado do v0.1 pra registro.
        """
        resp = requests.get(caption.url, timeout=30)
        resp.raise_for_status()
        return resp.text
