"""Interface de linha de comando."""

import argparse

from .client import UdemyClient
from .config import load_config, resolve_cookies
from .downloader import download_transcripts, list_available_captions
from .exceptions import UdemyTranscripterError
from .setup import setup_env
from .utils import extract_slug


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos."""
    parser = argparse.ArgumentParser(
        prog="udemy_transcripter",
        description="Extrai transcrições de cursos da Udemy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Configurar cookies (primeira vez)
  python -m udemy_transcripter --setup

  # Usando .env (após setup)
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/"

  # Listar idiomas disponíveis
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --list-langs

  # Baixar com timestamps + arquivo mesclado para IA
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --timestamps --merge

  # Depurar problemas de autenticação
  python -m udemy_transcripter --url "https://udemy.com/course/meu-curso/" --list-langs --debug
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
    """Ponto de entrada principal da CLI.

    Args:
        argv: Argumentos (usa sys.argv se None).

    Returns:
        Código de saída (0 = sucesso, 1 = erro).
    """
    load_config()
    parser = build_parser()
    args = parser.parse_args(argv)

    # Setup interativo
    if args.setup:
        setup_env()
        return 0

    # Resolver cookies
    cookie_data = resolve_cookies(args.cookie)

    if not cookie_data:
        print("✗ Cookies não encontrados.")
        print("  Opções:")
        print("    1. Crie um .env:  python -m udemy_transcripter --setup")
        print("    2. Passe via CLI: --cookie 'SUA_COOKIE_STRING'")
        return 1

    if not args.url:
        parser.error("--url é obrigatório (a menos que use --setup)")

    slug = extract_slug(args.url)
    client = UdemyClient(cookie_data, debug=args.debug)

    if args.debug:
        display = cookie_data[:30] + "..." if len(cookie_data) > 30 else cookie_data
        print(f"[DEBUG] Cookie data: {display} ({len(cookie_data)} chars)")
        print(f"[DEBUG] Slug: {slug}")
        print()

    # Executa o comando
    try:
        if args.list_langs:
            list_available_captions(client, slug)
        else:
            download_transcripts(
                client=client,
                slug=slug,
                output_dir=args.output,
                lang=args.lang,
                with_timestamps=args.timestamps,
                merge=args.merge,
            )
    except UdemyTranscripterError as e:
        print(f"\n✗ {e}")
        if args.debug:
            raise
        return 1

    return 0