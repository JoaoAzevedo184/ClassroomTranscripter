"""CLI da Alura: `classroom-alura` ou `classroom alura`.

IMPLEMENTAÇÃO (Fase 7):
----------------------
Flags específicas:
  --url / -u URL            URL do curso
  --email EMAIL             (ou ALURA_EMAIL via .env)
  --password PASSWORD       (ou ALURA_PASSWORD via .env — prefira .env!)
  --format / -f {txt,obsidian}
  --output / -o PATH
  --merge / -m
  --debug

Exemplo:
    classroom-alura --url "https://cursos.alura.com.br/course/..." --format obsidian

Se --password ausente, ler de .env. Se .env tbm não tiver, pedir via getpass (interativo).
"""
from __future__ import annotations


def main() -> int:
    raise NotImplementedError("Implementar na Fase 7")


if __name__ == "__main__":
    raise SystemExit(main())
