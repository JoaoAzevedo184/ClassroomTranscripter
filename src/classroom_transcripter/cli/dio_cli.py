"""CLI da DIO: `classroom-dio` ou `classroom dio`.

IMPLEMENTAÇÃO (Fase 6):
----------------------
Flags específicas:
  --video-dir PATH         pasta raiz do bootcamp baixado (obrigatório)
  --whisper-model {tiny,base,small,medium,large}   (padrão: small)
  --lang / -l LANG          (padrão: pt)
  --format / -f {txt,obsidian}  (padrão: obsidian)
  --output / -o PATH        (padrão: ./transcripts/dio)
  --timestamps / -t         (Whisper sempre dá segments, então --timestamps é natural aqui)
  --merge / -m
  --debug

Exemplo:
    classroom-dio \\
      --video-dir ~/dio_videos/jornada-node \\
      --whisper-model small \\
      --format obsidian --merge
"""
from __future__ import annotations


def main() -> int:
    raise NotImplementedError("Implementar na Fase 6")


if __name__ == "__main__":
    raise SystemExit(main())
