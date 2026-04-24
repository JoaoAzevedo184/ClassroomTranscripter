"""Source da Alura: login + API + parsing de transcript."""
from classroom_transcripter.sources.alura.client import AluraClient
from classroom_transcripter.sources.alura.parser import parse_course, parse_transcript
from classroom_transcripter.sources.alura.source import AluraSource

__all__ = ["AluraClient", "AluraSource", "parse_course", "parse_transcript"]
