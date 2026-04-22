"""Descoberta da estrutura de um bootcamp DIO a partir de arquivos locais.

A DIO não tem API pública, então o "curso" é inferido da organização dos .mp4
que o usuário baixou. Convenção obrigatória:

**Estrutura profunda** — cada subpasta = um módulo, cada .mp4 dentro = aula:

    my-bootcamp/
    ├── 01-fundamentos/
    │   ├── 01-introducao.mp4
    │   └── 02-variaveis.mp4
    ├── 02-apis/
    │   └── 01-intro-rest.mp4
    └── 03-banco-de-dados/
        └── 01-sql.mp4

Se o path passado não tem subpastas com vídeos, levanta `CourseNotFoundError`
com instruções de como organizar os arquivos.
"""
from __future__ import annotations

import re
from pathlib import Path

from classroom_transcripter.core.exceptions import CourseNotFoundError
from classroom_transcripter.core.models import Course, Lecture, Module


# Extensões de vídeo/áudio que o Whisper aceita via ffmpeg
SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4a", ".mp3", ".wav"}


def discover_course(root: Path) -> Course:
    """Varre a pasta `root` e devolve um `Course` com módulos + aulas inferidos.

    Args:
        root: path pro bootcamp/curso baixado. Deve conter subpastas
              (uma por módulo).

    Returns:
        Course pronto pra passar ao downloader.

    Raises:
        CourseNotFoundError: se a pasta não existir, estiver sem subpastas,
            ou nenhuma das subpastas tiver vídeos.
    """
    root = Path(root).expanduser().resolve()

    if not root.is_dir():
        raise CourseNotFoundError(f"Pasta não encontrada: {root}")

    subdirs = sorted(
        [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")],
        key=lambda p: _natural_sort_key(p.name),
    )

    if not subdirs:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise CourseNotFoundError(
            f"{root} não contém subpastas de módulos.\n"
            f"  Estrutura esperada:\n"
            f"    {root.name}/\n"
            f"    ├── 01-nome-do-modulo/\n"
            f"    │   ├── 01-aula.mp4\n"
            f"    │   └── 02-aula.mp4\n"
            f"    └── 02-outro-modulo/\n"
            f"        └── ...\n"
            f"  Extensões aceitas: {exts}"
        )

    modules = _build_modules(subdirs)

    total_lectures = sum(len(m.lectures) for m in modules)
    if total_lectures == 0:
        exts = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise CourseNotFoundError(
            f"Nenhum vídeo encontrado nas subpastas de {root}.\n"
            f"  Extensões suportadas: {exts}"
        )

    return Course(
        id=root.name,
        slug=_slugify_dir_name(root.name),
        title=_prettify_name(root.name),
        platform="dio",
        modules=modules,
        metadata={"root": str(root)},
    )


# ─── Internos ───────────────────────────────────────────────────────────────


def _build_modules(module_dirs: list[Path]) -> list[Module]:
    """Uma subpasta = um módulo. Subpastas sem vídeos são ignoradas."""
    modules: list[Module] = []
    for idx, module_dir in enumerate(module_dirs, start=1):
        videos = _find_videos(module_dir)
        if not videos:
            continue
        lectures = _videos_to_lectures(videos)
        modules.append(
            Module(
                title=_prettify_name(module_dir.name),
                index=idx,
                lectures=lectures,
            )
        )
    return modules


def _find_videos(directory: Path) -> list[Path]:
    """Lista arquivos com extensão suportada, ordenados por nome natural."""
    return sorted(
        [
            f for f in directory.iterdir()
            if f.is_file()
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
            and not f.name.startswith(".")
        ],
        key=lambda p: _natural_sort_key(p.name),
    )


def _videos_to_lectures(videos: list[Path]) -> list[Lecture]:
    """Converte paths em Lectures, colocando o path no `metadata['file']`.

    O `metadata['file']` é como `DioSource.fetch_transcript` localiza o .mp4
    pra mandar pro Whisper. Esse mesmo campo é o que `core.downloader.
    _lecture_is_available` checa pra reconhecer aulas DIO.
    """
    return [
        Lecture(
            id=_file_id(video),
            title=_prettify_name(video.stem),
            object_index=idx,
            metadata={"file": str(video)},
        )
        for idx, video in enumerate(videos, start=1)
    ]


def _file_id(video: Path) -> str:
    """ID estável baseado no path relativo do arquivo.

    Usar path (não hash) mantém IDs legíveis em logs/metadata.json.
    """
    return video.name


def _natural_sort_key(name: str) -> list:
    """Ordena '01-x', '02-y', '10-z' corretamente (não '01', '10', '02')."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", name)
    ]


def _prettify_name(raw: str) -> str:
    """Transforma '01-introducao-ao-node' em 'Introdução ao Node' (mais ou menos).

    - Remove prefixo numérico (`01-`, `02 -`, etc)
    - Troca hífens/underlines por espaços
    - Capitaliza palavras
    - Não tenta acentuar (não dá pra adivinhar) — mantém como está depois do split
    """
    # Remove prefixo numérico opcional: "01-", "01 -", "01_"
    cleaned = re.sub(r"^\d+[\s\-_]*", "", raw)
    # Normaliza separadores
    cleaned = re.sub(r"[\-_]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return raw
    # Capitaliza primeira letra de cada palavra
    return " ".join(word[:1].upper() + word[1:] for word in cleaned.split(" "))


def _slugify_dir_name(name: str) -> str:
    """'My Bootcamp Node.js' → 'my-bootcamp-node.js' (pra slug do Course)."""
    s = name.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s
