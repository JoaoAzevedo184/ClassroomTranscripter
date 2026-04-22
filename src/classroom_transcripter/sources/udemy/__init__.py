"""Source da Udemy: cookies + API interna + VTT."""
from classroom_transcripter.sources.udemy.client import UdemyClient
from classroom_transcripter.sources.udemy.parser import build_course
from classroom_transcripter.sources.udemy.source import UdemySource

__all__ = ["UdemyClient", "UdemySource", "build_course"]
