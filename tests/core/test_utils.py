"""Testes dos utils (extract_slug, sanitize_filename, pick_caption)."""
from classroom_transcripter.core.models import Caption
from classroom_transcripter.core.utils import extract_slug, pick_caption, sanitize_filename


# ─── extract_slug ──────────────────────────────────────────────────────────


def test_extract_slug_udemy_url():
    assert extract_slug("https://www.udemy.com/course/docker-basico/") == "docker-basico"


def test_extract_slug_udemy_with_query():
    assert extract_slug("https://udemy.com/course/python/?ref=abc") == "python"


def test_extract_slug_plain():
    assert extract_slug("docker-basico") == "docker-basico"


def test_extract_slug_alura():
    assert extract_slug("https://cursos.alura.com.br/course/docker-fund") == "docker-fund"


# ─── sanitize_filename ─────────────────────────────────────────────────────


def test_sanitize_filename_removes_invalid_chars():
    assert sanitize_filename('Aula 1: Introdução ao "Docker"') == "Aula 1 Introdução ao Docker"


def test_sanitize_filename_collapses_whitespace():
    assert sanitize_filename("a    b     c") == "a b c"


def test_sanitize_filename_respects_max_length():
    long = "a" * 200
    assert len(sanitize_filename(long, max_length=50)) == 50


def test_sanitize_filename_removes_slashes_and_pipes():
    assert sanitize_filename("foo/bar|baz") == "foobarbaz"


# ─── pick_caption ──────────────────────────────────────────────────────────


def test_pick_caption_empty():
    assert pick_caption([]) is None


def test_pick_caption_preferred_language():
    caps = [
        Caption(locale="en", url="u1", label="EN"),
        Caption(locale="pt", url="u2", label="PT"),
    ]
    picked = pick_caption(caps, preferred_lang="pt")
    assert picked is not None
    assert picked.locale == "pt"


def test_pick_caption_preferred_language_case_insensitive():
    caps = [Caption(locale="PT-BR", url="u", label="X")]
    assert pick_caption(caps, preferred_lang="pt") == caps[0]


def test_pick_caption_fallback_lang_priority():
    """Sem lang explícita, segue LANG_PRIORITY (pt tem prioridade)."""
    caps = [
        Caption(locale="fr", url="u1", label="FR"),
        Caption(locale="pt", url="u2", label="PT"),
    ]
    assert pick_caption(caps).locale == "pt"


def test_pick_caption_no_match_returns_first():
    """Se nada bate, volta a primeira disponível."""
    caps = [Caption(locale="ja", url="u1", label="JA")]
    assert pick_caption(caps) == caps[0]
