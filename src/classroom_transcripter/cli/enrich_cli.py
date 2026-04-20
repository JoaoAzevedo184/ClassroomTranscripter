"""CLI de enriquecimento: `classroom-enrich` ou `classroom enrich`.

MIGRAÇÃO (Fase 5):
-----------------
Migrar do `udemy_transcripter/cli.py` só as flags de enriquecimento:
  <dir>                     pasta com .md gerados (posicional, obrigatório)
  --provider {groq,gemini,ollama,claude}  (padrão: groq)
  --model MODEL
  --api-key KEY
  --ollama-url URL
  --delay SEC               (padrão: 1.0)
  --dry-run
  --debug

O comando é AGNÓSTICO de plataforma: funciona em pasta gerada por udemy,
dio ou alura. Isso é um benefício direto da refatoração.
"""
from __future__ import annotations


def main() -> int:
    # TODO Fase 5: migrar lógica do --enrich do cli.py atual
    raise NotImplementedError("Migrar na Fase 5")


if __name__ == "__main__":
    raise SystemExit(main())
