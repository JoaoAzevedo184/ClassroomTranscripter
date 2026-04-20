"""CLI umbrella: `classroom <subcomando> ...`

Despacha pros CLIs específicos de cada plataforma + o enrich.
Permite dois estilos de uso:

  # Estilo 1: comandos separados (já registrados em pyproject [project.scripts])
  classroom-udemy --url ... --format obsidian
  classroom-dio --video-dir ./dio_videos/java-bootcamp
  classroom-alura --url ...
  classroom-enrich ./transcripts/MeuCurso --provider groq

  # Estilo 2: comando umbrella
  classroom udemy --url ... --format obsidian
  classroom dio --video-dir ...
  classroom alura --url ...
  classroom enrich ./transcripts/MeuCurso --provider groq
"""
from __future__ import annotations

import sys


USAGE = """\
Classroom Transcripter — transcrições de cursos com IA

Uso:
  classroom udemy   [opções]        Transcrever curso da Udemy
  classroom dio     [opções]        Transcrever bootcamp da DIO (Whisper local)
  classroom alura   [opções]        Transcrever curso da Alura
  classroom enrich  <dir> [opções]  Enriquecer transcripts com IA

Use `classroom <subcomando> --help` pra ver opções de cada plataforma.
"""


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print(USAGE)
        return 0

    subcommand = sys.argv[1]
    # Remove o subcomando de argv pra cada CLI específico achar só suas próprias flags
    sys.argv = [sys.argv[0], *sys.argv[2:]]

    if subcommand == "udemy":
        from classroom_transcripter.cli.udemy_cli import main as udemy_main
        return udemy_main()
    if subcommand == "dio":
        from classroom_transcripter.cli.dio_cli import main as dio_main
        return dio_main()
    if subcommand == "alura":
        from classroom_transcripter.cli.alura_cli import main as alura_main
        return alura_main()
    if subcommand == "enrich":
        from classroom_transcripter.cli.enrich_cli import main as enrich_main
        return enrich_main()

    print(f"Subcomando desconhecido: {subcommand!r}\n", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
