"""CLI da Alura: `classroom-alura` ou `classroom alura`.

Exemplos:
    # Credenciais via .env (ALURA_EMAIL + ALURA_PASSWORD)
    classroom-alura --url "https://cursos.alura.com.br/course/docker-fundamentos" \\
      --format obsidian --merge

    # Credenciais via CLI (menos seguro — fica no histórico do shell)
    classroom-alura --url "..." --email e@x.com --password "senha"

    # Retomar download interrompido
    classroom-alura --url "..." --resume
"""
from __future__ import annotations

import argparse
import getpass

from classroom_transcripter.core.config import get_alura_credentials, load_config
from classroom_transcripter.core.downloader import download_course
from classroom_transcripter.core.exceptions import TranscripterError
from classroom_transcripter.core.formatters import FORMATTERS, get_formatter
from classroom_transcripter.sources.alura import AluraSource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classroom-alura",
        description="Extrai transcrições de cursos da Alura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Credenciais via .env (recomendado)
  classroom-alura --url "https://cursos.alura.com.br/course/docker-fundamentos"

  # Credenciais via CLI
  classroom-alura --url "..." --email e@x.com

  # Interativo (senha digitada sem aparecer)
  classroom-alura --url "..." --email e@x.com --ask-password

Configuração .env:
  ALURA_EMAIL=seu@email.com
  ALURA_PASSWORD=sua-senha
        """,
    )

    parser.add_argument(
        "--url", "-u", required=True,
        help="URL do curso Alura ou slug (ex: docker-fundamentos)",
    )
    parser.add_argument(
        "--email", "-e", default=None,
        help="Email de login (default: ALURA_EMAIL do .env)",
    )
    parser.add_argument(
        "--password", "-p", default=None,
        help="Senha (default: ALURA_PASSWORD do .env — PREFIRA isso)",
    )
    parser.add_argument(
        "--ask-password", action="store_true",
        help="Perguntar a senha interativamente (não fica no histórico)",
    )
    parser.add_argument(
        "--output", "-o", default="./alura_transcripts",
        help="Diretório de saída (padrão: ./alura_transcripts)",
    )
    parser.add_argument(
        "--format", "-f", default="obsidian", choices=FORMATTERS.keys(),
        help="Formato: obsidian (padrão) ou txt",
    )
    parser.add_argument(
        "--lang", "-l", default="pt",
        help="Idioma default pro Transcript (padrão: pt)",
    )
    parser.add_argument(
        "--timestamps", "-t", action="store_true",
        help="Incluir timestamps no texto (quando disponíveis)",
    )
    parser.add_argument(
        "--merge", "-m", action="store_true",
        help="Gerar arquivo único com todo o curso",
    )
    parser.add_argument(
        "--resume", "-r", action="store_true",
        help="Pular aulas cujo .md já existe",
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

    # Resolve credenciais: CLI > .env > prompt
    env_email, env_password = get_alura_credentials()
    email = args.email or env_email
    password = args.password or env_password

    if args.ask_password:
        password = getpass.getpass("Senha Alura: ")

    if not email:
        print("✗ Email não encontrado.")
        print("  Opções:")
        print("    1. ALURA_EMAIL no .env")
        print("    2. --email ...")
        return 1
    if not password:
        print("✗ Senha não encontrada.")
        print("  Opções:")
        print("    1. ALURA_PASSWORD no .env (recomendado)")
        print("    2. --password ... (fica no histórico do shell)")
        print("    3. --ask-password (prompt interativo)")
        return 1

    if args.debug:
        print(f"[DEBUG] Email: {email}")
        print(f"[DEBUG] URL: {args.url}")
        print(f"[DEBUG] Formato: {args.format}")
        print()

    source = AluraSource(
        email=email,
        password=password,
        language=args.lang,
        debug=args.debug,
    )

    formatter_kwargs = {"platform": "alura"} if args.format == "obsidian" else {}
    formatter = get_formatter(args.format, **formatter_kwargs)

    try:
        course = source.fetch_course(args.url)
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
    except NotImplementedError as e:
        print("\n✗ Fase 7 ainda não foi completada.")
        print(f"  {e}")
        print("\n  Pra ativar Alura:")
        print("    1. Abra docs/sources/alura.md")
        print("    2. Siga o passo-a-passo de inspeção no DevTools")
        print("    3. Preencha os 3 TODOs em sources/alura/client.py")
        return 1
    except TranscripterError as e:
        print(f"\n✗ {e}")
        if args.debug:
            raise
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
