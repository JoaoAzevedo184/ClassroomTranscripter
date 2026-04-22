"""CLI de enriquecimento: `classroom-enrich` ou `classroom enrich`.

Enriquece notas .md geradas por QUALQUER source (Udemy, DIO, Alura) com IA.

Exemplos:
    # Ollama local (gratuito, rodando no teu homelab)
    classroom-enrich ./udemy_transcripts/MeuCurso --provider ollama

    # Groq (nuvem, gratuito, ultra-rápido)
    classroom-enrich ./dio_transcripts/JornadaNode --provider groq

    # Modelo específico do Ollama
    classroom-enrich ./transcripts/X --provider ollama --model qwen2.5:14b

    # Gemini (gratuito, sem cartão)
    classroom-enrich ./transcripts/X --provider gemini

    # Claude (pago)
    classroom-enrich ./transcripts/X --provider claude

    # Preview sem alterar arquivos
    classroom-enrich ./transcripts/X --provider ollama --dry-run
"""
from __future__ import annotations

import argparse
from pathlib import Path

from classroom_transcripter.core.config import load_config
from classroom_transcripter.core.enricher import create_provider, enrich_directory
from classroom_transcripter.core.exceptions import TranscripterError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="classroom-enrich",
        description="Enriquece notas .md com IA (agnóstico de plataforma)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Providers disponíveis:
  ollama  — local via Ollama, gratuito (padrão)
  groq    — nuvem, gratuito, ultra-rápido
  gemini  — nuvem, gratuito, sem cartão
  claude  — nuvem, pago, alta qualidade

Exemplos:
  classroom-enrich ./transcripts/MeuCurso --provider groq
  classroom-enrich ./transcripts/X --provider ollama --model qwen2.5:14b
  classroom-enrich ./transcripts/X --provider gemini --dry-run
        """,
    )

    parser.add_argument(
        "directory",
        help="Diretório com .md gerados pelo download",
    )
    parser.add_argument(
        "--provider", "-p",
        default="ollama",
        choices=["ollama", "claude", "groq", "gemini"],
        help="Provider de IA (padrão: ollama)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Modelo (ex: llama3.1, llama-3.3-70b-versatile, claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="API key (padrão: lê do .env — GROQ_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--ollama-url", default=None,
        help="URL do Ollama (padrão: http://localhost:11434)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Delay entre chamadas de IA em segundos (padrão: 1.0)",
    )
    parser.add_argument(
        "--timeout", type=int, default=900,
        help="Timeout por requisição em segundos (padrão: 900, relevante para Ollama)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview do enriquecimento sem alterar arquivos",
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

    enrich_dir = Path(args.directory)
    if not enrich_dir.is_dir():
        print(f"✗ Diretório não encontrado: {enrich_dir}")
        return 1

    try:
        provider = create_provider(
            provider_name=args.provider,
            model=args.model,
            api_key=args.api_key,
            base_url=args.ollama_url,
            timeout=args.timeout,
        )
    except (ValueError, TranscripterError) as e:
        print(f"✗ {e}")
        return 1

    try:
        enrich_directory(
            directory=enrich_dir,
            provider=provider,
            delay=args.delay,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"\n✗ Erro no enriquecimento: {e}")
        if args.debug:
            raise
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
