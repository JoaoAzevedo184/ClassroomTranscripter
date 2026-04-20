"""Parsing de respostas da Alura pra Course/Module/Lecture/Transcript.

IMPLEMENTAÇÃO (Fase 7):
----------------------
Depende do formato que a API/HTML da Alura devolve (ver client.py).

Funções esperadas:
- parse_course(raw) -> Course
- parse_transcript(raw) -> Transcript  (pode ser texto corrido OU com timestamps)

NOTA: se a Alura expõe transcript APENAS em HTML (sem timestamps), o Transcript
resultante terá `plain_text` preenchido e `cues=[]`. Isso é OK — os formatters
já tratam esse caso via `transcript.has_timestamps`.
"""
# TODO Fase 7
