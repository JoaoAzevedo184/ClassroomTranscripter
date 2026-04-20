"""CLI da Udemy: `classroom-udemy` ou `classroom udemy`.

MIGRAÇÃO (Fase 5):
-----------------
Migrar do atual `udemy_transcripter/cli.py` só as flags específicas da Udemy:
  --url / -u, --lang / -l, --list-langs, --timestamps / -t,
  --merge / -m, --output / -o, --format / -f, --cookie / -c,
  --setup, --debug

REMOVER daqui:
  --enrich, --provider, --model, --api-key, --ollama-url, --delay, --dry-run
  → Esses viram `classroom enrich` em `enrich_cli.py`.

ESTRUTURA:
    parser = argparse.ArgumentParser(prog="classroom-udemy", ...)
    ... add_argument ...
    args = parser.parse_args()

    source = UdemySource(cookie=args.cookie or config.UDEMY_COOKIE)
    source.authenticate()
    course = source.fetch_course(args.url)
    formatter = get_formatter(args.format)
    # usa o downloader genérico do core (Fase 4)
    download_course(source, course, formatter, output_dir=args.output, ...)
"""
from __future__ import annotations


def main() -> int:
    # TODO Fase 5: migrar argparse e lógica do cli.py atual
    raise NotImplementedError("Migrar na Fase 5")


if __name__ == "__main__":
    raise SystemExit(main())
