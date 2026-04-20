"""Parser de legendas WebVTT.

MIGRAÇÃO (Fase 2):
-----------------
Copiar o conteúdo atual de `udemy_transcripter/vtt.py` inteiro.
Este módulo é plataforma-agnóstico: Udemy e Alura ambos expõem VTT.
DIO usa Whisper (não VTT), então não toca esse arquivo.

API que deve continuar existindo:
- parse_vtt(content: str) -> list[TranscriptCue]  (adaptar pra retornar TranscriptCue do core/models)
- vtt_to_plain_text(content: str) -> str
"""
# TODO Fase 2: migrar udemy_transcripter/vtt.py e adaptar tipos de retorno
# pra TranscriptCue de core.models
