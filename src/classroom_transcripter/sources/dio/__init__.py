"""Source da DIO: Whisper local sobre .mp4 baixados."""
from classroom_transcripter.sources.dio.source import DioSource
from classroom_transcripter.sources.dio.video_finder import discover_course
from classroom_transcripter.sources.dio.whisper_engine import transcribe

__all__ = ["DioSource", "discover_course", "transcribe"]
