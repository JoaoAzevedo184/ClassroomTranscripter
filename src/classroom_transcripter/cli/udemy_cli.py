"""CLI da Udemy: `classroom-udemy` ou `classroom udemy`.

Substitui o `python -m udemy_transcripter` do v0.1 com a mesma UX, mas agora
consumindo `UdemySource` + downloader genérico por baixo.

Exemplos:
    # Configurar cookies (primeira vez)
    classroom-udemy --setup

    # Download como Markdown para Obsidian
    classroom-udemy --url "https://udemy.com/course/meu-curso/" --format obsidian

    # Retomar download interrompido
    classroom-udemy --url "..." --resume

    # Só listar idiomas disponíveis
    classroom-udemy --url "..." --list-langs
"""
from __future__ import annotations

import argparse

from classroom_transcripter.core.config import load_config, resolve_cookies
from classroom_transcripter.core.downloader import (
    download_course,
    list_available_captions,
)
from classroom_transcripter.core.exceptions import TranscripterError
from classroom_transcripter.core.formatters import FORMATTERS, get_formatter
from classroom_transcripter.sources.udemy import UdemySource


def build_parser() -> argparse.ArgumentParser:
    available_formats = ", ".join(FORMATTERS.keys())

    parser = argparse.ArgumentParser(
        prog="classroom-udemy",
        description="Extrai transcrições de cursos da Udemy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Exemplos:
  # Configurar cookies (primeira vez)
  classroom-udemy --setup

  # Download como Markdown para Obsidian
  classroom-udemy --url "https://udemy.com/course/meu-curso/" --format obsidian --merge

  # Retomar download interrompido
  classroom-udemy --url "..." --resume

  # Listar idiomas de legenda disponíveis
  classroom-udemy --url "..." --list-langs

Formatos disponíveis: {available_formats}
Para enriquecer as notas com IA depois do download, use: classroom-enrich
        """,
    )

    parser.add_argument(
        "--cookie", "-c", default=None,
        help="String completa de cookies do navegador (opcional se usar .env)",
    )
    parser.add_argument(
        "--url", "-u", default=None,
        help="URL do curso ou slug (ex: python-bootcamp)",
    )
    parser.add_argument(
        "--output", "-o", default="./udemy_transcripts",
        help="Diretório de saída (padrão: ./udemy_transcripts)",
    )
    parser.add_argument(
        "--format", "-f", default="txt", choices=FORMATTERS.keys(),
        help="Formato de saída: txt (padrão) ou obsidian",
    )
    parser.add_argument(
        "--lang", "-l", default=None,
        help="Idioma preferido (ex: pt, en, es)",
    )
    parser.add_argument(
        "--timestamps", "-t", action="store_true",
        help="Incluir timestamps no texto",
    )
    parser.add_argument(
        "--merge", "-m", action="store_true",
        help="Gerar arquivo único com todo o curso (ideal para IA)",
    )
    parser.add_argument(
        "--resume", "-r", action="store_true",
        help="Retomar download interrompido (pula aulas já baixadas)",
    )
    parser.add_argument(
        "--list-langs", action="store_true",
        help="Apenas listar idiomas de legenda disponíveis",
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="Criar/atualizar arquivo .env interativamente",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Exibir detalhes das requisições para depuração",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal do CLI Udemy.

    Args:
        argv: argumentos (usa sys.argv se None).

    Returns:
        Código de saída (0 = sucesso, 1 = erro).
    """
    load_config()
    parser = build_parser()
    args = parser.parse_args(argv)

    # ─── --setup ────────────────────────────────────────────────────────
    if args.setup:
        from classroom_transcripter.cli.setup_cli import setup_env
        setup_env()
        return 0

    # ─── Download normal ────────────────────────────────────────────────
    cookie_data = resolve_cookies(args.cookie)

    if not cookie_data:
        print("✗ Cookies não encontrados.")
        print("  Opções:")
        print("    1. Crie um .env:  classroom-udemy --setup")
        print("    2. Passe via CLI: --cookie 'SUA_COOKIE_STRING'")
        return 1

    if not args.url:
        parser.error("--url é obrigatório (a menos que use --setup)")

    # Debug header
    if args.debug:
        display = cookie_data[:30] + "..." if len(cookie_data) > 30 else cookie_data
        print(f"[DEBUG] Cookie data: {display} ({len(cookie_data)} chars)")
        print(f"[DEBUG] URL: {args.url}")
        print(f"[DEBUG] Formato: {args.format}")
        print(f"[DEBUG] Resume: {args.resume}")
        print()

    source = UdemySource(cookie=cookie_data, language=args.lang or "pt", debug=args.debug)

    # Formatter: pra Obsidian, passa platform=udemy pro frontmatter dinâmico
    formatter_kwargs = {"platform": "udemy"} if args.format == "obsidian" else {}
    formatter = get_formatter(args.format, **formatter_kwargs)

    try:
        course = source.fetch_course(args.url)

        if args.list_langs:
            list_available_captions(source, course)
            return 0

        download_course(
            source,
            course,
            output_dir=args.output,
            lang=args.lang,
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
