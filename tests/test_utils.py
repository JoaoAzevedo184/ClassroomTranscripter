"""Testes das funções utilitárias."""

from udemy_transcripter.models import Caption
from udemy_transcripter.utils import extract_slug, pick_caption, sanitize_filename


class TestExtractSlug:
    def test_full_url(self):
        url = "https://www.udemy.com/course/docker-basico/"
        assert extract_slug(url) == "docker-basico"

    def test_url_with_params(self):
        url = "https://www.udemy.com/course/python-pro/?couponCode=ABC"
        assert extract_slug(url) == "python-pro"

    def test_plain_slug(self):
        assert extract_slug("docker-basico") == "docker-basico"

    def test_slug_with_trailing_slash(self):
        assert extract_slug("docker-basico/") == "docker-basico"


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert sanitize_filename('Aula: "Intro"') == "Aula Intro"

    def test_collapses_whitespace(self):
        assert sanitize_filename("Aula   com    espaços") == "Aula com espaços"

    def test_truncates_long_names(self):
        name = "A" * 200
        assert len(sanitize_filename(name)) == 100

    def test_custom_max_length(self):
        assert len(sanitize_filename("A" * 50, max_length=30)) == 30


class TestPickCaption:
    def _make_captions(self) -> list[Caption]:
        return [
            Caption(locale="en_US", url="http://en.vtt", label="English"),
            Caption(locale="pt_BR", url="http://pt.vtt", label="Português"),
            Caption(locale="es_ES", url="http://es.vtt", label="Español"),
        ]

    def test_returns_none_for_empty(self):
        assert pick_caption([]) is None

    def test_preferred_lang(self):
        cap = pick_caption(self._make_captions(), "es")
        assert cap.locale == "es_ES"

    def test_priority_fallback(self):
        cap = pick_caption(self._make_captions())
        assert cap.locale == "pt_BR"  # "pt" é prioridade na LANG_PRIORITY

    def test_first_available_as_last_resort(self):
        captions = [Caption(locale="ja", url="http://ja.vtt", label="日本語")]
        cap = pick_caption(captions)
        assert cap.locale == "ja"