"""Classroom Transcripter — ferramenta multi-plataforma para transcrição e enriquecimento de cursos.

Suporta Udemy, DIO e Alura. Pipeline: download/transcribe → format → enrich (IA).

Uso como biblioteca:
    from classroom_transcripter.sources.udemy import UdemySource
    from classroom_transcripter.core.formatters import ObsidianFormatter
    from classroom_transcripter.core.enricher import create_provider

    source = UdemySource(cookie="...")
    course = source.fetch_course("meu-curso")
    ...
"""

__version__ = "0.2.0"
