"""Descoberta da estrutura de um bootcamp/curso DIO a partir de arquivos locais.

MIGRAÇÃO (Fase 6):
-----------------
Lógica NOVA — DIO não tem API pública de curriculum, então inferimos
a estrutura a partir de convenções de nomenclatura de pastas/arquivos.

Convenção sugerida que o usuário segue ao baixar os vídeos:
    <DIO_VIDEO_DIR>/
    └── <nome-do-bootcamp>/
        ├── 01-modulo-fundamentos/
        │   ├── 01-introducao.mp4
        │   ├── 02-instalacao.mp4
        │   └── ...
        ├── 02-modulo-apis/
        │   └── ...

Funções esperadas:
- discover_course(root: Path) -> Course
  (lê a árvore, monta Course/Module/Lecture a partir dos nomes)
- natural_sort_key(name: str)  (pra ordenar 01, 02, ..., 10 corretamente)

Os Lectures ficam com `source_url = None` e `metadata = {'file': Path(...)}`
pra o whisper_engine saber qual arquivo transcrever.
"""
from __future__ import annotations

from pathlib import Path

from classroom_transcripter.core.models import Course


def discover_course(root: Path, *, platform: str = "dio") -> Course:
    """TODO Fase 6: varrer a pasta e montar Course a partir da convenção."""
    raise NotImplementedError("Fase 6: implementar descoberta por convenção de pastas")
