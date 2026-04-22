"""Helpers de parsing específicos da API Udemy.

O parsing de ITENS individuais (chapter/lecture/caption) já vive em
`UdemyClient._parse_lecture` e `UdemyClient.get_curriculum` — esses métodos
lidam diretamente com o formato paginado da API.

Este módulo existe pra hospedar montagens de ALTO NÍVEL: combinar os pedaços
(course_info + curriculum) num `Course` completo e agnóstico.
"""
from __future__ import annotations

from classroom_transcripter.core.models import Course, Module


def build_course(
    course_id: int,
    title: str,
    slug: str,
    modules: list[Module],
    *,
    language: str | None = None,
) -> Course:
    """Monta um `Course` a partir das partes que o `UdemyClient` devolve.

    Args:
        course_id: ID numérico da Udemy.
        title: título do curso.
        slug: slug do curso (pra reconstruir URL pública depois).
        modules: lista de módulos vinda de `UdemyClient.get_curriculum`.
        language: código de idioma principal, se conhecido.

    Returns:
        Course com `platform="udemy"` e todos os módulos/aulas populados.
    """
    return Course(
        id=course_id,
        slug=slug,
        title=title,
        platform="udemy",
        modules=modules,
        language=language,
        metadata={"api": "udemy"},
    )
