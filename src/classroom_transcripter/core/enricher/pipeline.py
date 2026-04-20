"""Orquestração do enriquecimento: varre pastas, chama provider, grava resultado.

MIGRAÇÃO (Fase 2):
-----------------
Migrar do atual `udemy_transcripter/enricher.py`:
- Função `enrich_directory(path, provider, *, delay, dry_run)`
- Função `enrich_file(path, provider, *, dry_run)`
- Constante SYSTEM_PROMPT (o prompt master que pede markdown obsidian-ready)

A lógica de CHAMADA DO LLM sai daqui e vai pra `providers/*.py`.
Este arquivo fica SÓ com orquestração + prompt.
"""
# TODO Fase 2: migrar orquestração de udemy_transcripter/enricher.py


def enrich_directory(*args, **kwargs):
    raise NotImplementedError("Migrar na Fase 2")


def enrich_file(*args, **kwargs):
    raise NotImplementedError("Migrar na Fase 2")
