"""Módulos de fonte por plataforma.

Cada subpacote (udemy, dio, alura) implementa `TranscriptSource` do jeito dele,
mas todos falam o mesmo "idioma" (Course/Module/Lecture/Transcript do core.models).

Isso permite que o downloader, os formatters e o enricher sejam totalmente
agnósticos de plataforma.
"""
from classroom_transcripter.sources.base import TranscriptSource

__all__ = ["TranscriptSource"]
