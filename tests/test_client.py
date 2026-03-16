"""Testes do cliente Udemy (parsing de cookies)."""

from udemy_transcripter.client import UdemyClient


class TestExtractCookieValue:
    def test_simple_value(self):
        cookies = "client_id=abc123; access_token=xyz789; cf_clearance=def"
        assert UdemyClient._extract_cookie_value(cookies, "access_token") == "xyz789"
        assert UdemyClient._extract_cookie_value(cookies, "client_id") == "abc123"
        assert UdemyClient._extract_cookie_value(cookies, "cf_clearance") == "def"

    def test_quoted_value(self):
        cookies = 'access_token="ABC:DEF/GHI"; client_id=123'
        result = UdemyClient._extract_cookie_value(cookies, "access_token")
        assert result == "ABC:DEF/GHI"

    def test_missing_cookie(self):
        cookies = "client_id=abc; cf_clearance=def"
        assert UdemyClient._extract_cookie_value(cookies, "access_token") is None

    def test_empty_string(self):
        assert UdemyClient._extract_cookie_value("", "access_token") is None

    def test_value_with_equals_sign(self):
        cookies = "access_token=abc=def; other=val"
        result = UdemyClient._extract_cookie_value(cookies, "access_token")
        assert result == "abc=def"