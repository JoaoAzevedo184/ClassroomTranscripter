"""Parsing da resposta da API Udemy pra Course/Module/Lecture.

MIGRAÇÃO (Fase 3):
-----------------
Extrair de `udemy_transcripter/downloader.py` (ou onde estiver) a lógica que:
- Recebe o JSON do endpoint de curriculum da Udemy
- Monta Course com seus Modules e Lectures

Essa parte mistura-se com `downloader.py` atual — precisa ISOLAR o parsing
da parte de I/O (download/salvamento). O I/O genérico vai pro core/downloader
na Fase 4; o parsing específico da API Udemy fica aqui.

Funções esperadas:
- parse_course_payload(json_data, slug) -> Course
- parse_captions_response(json_data) -> dict (para escolher língua/URL do VTT)
"""
# TODO Fase 3: isolar parsing da Udemy aqui
