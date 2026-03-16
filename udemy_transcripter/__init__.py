"""Udemy Transcript Extractor — extrai transcrições de cursos da Udemy."""

from .client import UdemyClient
from .downloader import download_transcripts, list_available_captions
from .models import Caption, DownloadResult, Lecture, Section

__all__ = [
    "UdemyClient",
    "download_transcripts",
    "list_available_captions",
    "Caption",
    "DownloadResult",
    "Lecture",
    "Section",
]