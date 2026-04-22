"""CLI da DIO: `classroom-dio` ou `classroom dio`.

Usa Whisper local pra transcrever .mp4 que você baixou manualmente.
Requer a instalação opcional `[dio]`: pip install 'classroom-transcripter[dio]'

Exemplos:
    # Transcrever bootcamp inteiro com Whisper small (padrão)
    classroom-dio --video-dir ~/dio_videos/jornada-node --format obsidian --merge

    # Modelo maior pra qualidade máxima (bem mais lento!)
    classroom-dio --video-dir ~/dio_videos/curso --whisper-model medium

    # Sem cache (transcrever do zero sempre)
    classroom-dio --video-dir ~/dio_videos/curso --no-cache

    # Idioma diferente
    classroom-dio --video-dir ~/dio_videos/curso-ingles --lang en
"""
from __future__ import annotations

import argparse

from classroom_transcripter.core.config import (
    get_whisper_language,
    get_whisper_model,
    load_config,
)
from classroom_transcripter.core.downloader import download_course
from classroom_transcripter.core.exceptions import TranscripterError
from classroom_transcripter.core.formatters import FORMATTERS, get_formatter
from classroom_transcripter.sources.dio import DioSource


WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classroom-dio",
        description="Transcreve bootcamps DIO com Whisper local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Exemplos:
  # Bootcamp com estrutura de módulos (01-fundamentos/, 02-apis/, etc)
  classroom-dio --video-dir ~/dio_videos/jornada-node --format obsidian --merge

  # Qualidade máxima (bem mais lento, exige mais RAM)
  classroom-dio --video-dir ~/dio_videos/curso --whisper-model medium

  # Curso em inglês
  classroom-dio --video-dir ~/dio_videos/curso-en --lang en

Modelos Whisper: {" | ".join(WHISPER_MODELS)}
Requer: pip install 'classroom-transcripter[dio]'
        """,
    )

    parser.add_argument(
        "--video-dir", "-d", required=True,
        help="Pasta raiz do bootcamp/curso baixado",
    )
    parser.add_argument(
        "--whisper-model", "-w", default=None,
        choices=WHISPER_MODELS,
        help="Modelo Whisper (default: small, ou WHISPER_MODEL do .env)",
    )
    parser.add_argument(
        "--lang", "-l", default=None,
        help="Idioma falado (default: pt, ou WHISPER_LANGUAGE do .env)",
    )
    parser.add_argument(
        "--output", "-o", default="./dio_transcripts",
        help="Diretório de saída (padrão: ./dio_transcripts)",
    )
    parser.add_argument(
        "--format", "-f", default="obsidian", choices=FORMATTERS.keys(),
        help="Formato: obsidian (padrão, já que DIO tem timestamps) ou txt",
    )
    parser.add_argument(
        "--timestamps", "-t", action="store_true",
        help="Incluir timestamps [HH:MM:SS] no texto",
    )
    parser.add_argument(
        "--merge", "-m", action="store_true",
        help="Gerar arquivo único com todo o curso",
    )
    parser.add_argument(
        "--resume", "-r", action="store_true",
        help="Pular aulas cujo .md já existe em disco (evita retranscrever tudo após crash)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Exibir stack trace em caso de erro",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    load_config()
    parser = build_parser()
    args = parser.parse_args(argv)

    whisper_model = args.whisper_model or get_whisper_model()
    language = args.lang or get_whisper_language()

    if args.debug:
        print(f"[DEBUG] video_dir: {args.video_dir}")
        print(f"[DEBUG] whisper_model: {whisper_model}")
        print(f"[DEBUG] language: {language}")
        print()

    source = DioSource(
        whisper_model=whisper_model,
        language=language,
    )

    formatter_kwargs = {"platform": "dio"} if args.format == "obsidian" else {}
    formatter = get_formatter(args.format, **formatter_kwargs)

    try:
        course = source.fetch_course(args.video_dir)
        download_course(
            source,
            course,
            output_dir=args.output,
            lang=language,
            with_timestamps=args.timestamps,
            merge=args.merge,
            formatter=formatter,
            resume=args.resume,
        )
    except TranscripterError as e:
        print(f"\n✗ {e}")
        if args.debug:
            raise
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
