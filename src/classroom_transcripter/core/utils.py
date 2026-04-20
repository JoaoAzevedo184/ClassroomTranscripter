"""Utilitários agnósticos de plataforma.

MIGRAÇÃO (Fase 2):
-----------------
Migrar de `udemy_transcripter/utils.py`:
- slugify(text) → filename-safe
- ensure_dir(path)
- format_duration(seconds)
- qualquer helper de filesystem que não seja específico de Udemy

SEPARAR (se houver no utils atual):
- Funções que mexem com cookie/API Udemy → mover pra `sources/udemy/`
- Funções específicas de VTT → já existe `core/vtt.py`
"""
# TODO Fase 2: migrar conteúdo agnóstico de udemy_transcripter/utils.py
