"""Testes da identificação de plataformas."""
import pytest

from classroom_transcripter.core.platforms import (
    AluraPlatform,
    BasePlatform,
    DioPlatform,
    UdemyPlatform,
    detect_platform,
    get_platform,
)


def test_udemy_extract_slug_from_url():
    assert UdemyPlatform().extract_slug("https://www.udemy.com/course/docker/") == "docker"
    assert UdemyPlatform().extract_slug("https://udemy.com/course/python-bootcamp/?ref=123") == "python-bootcamp"


def test_udemy_extract_slug_pass_through():
    assert UdemyPlatform().extract_slug("docker-basico") == "docker-basico"


def test_udemy_matches():
    assert UdemyPlatform().matches_url("https://udemy.com/course/x/") is True
    assert UdemyPlatform().matches_url("https://alura.com.br") is False


def test_dio_extract_slug_from_path():
    assert DioPlatform().extract_slug("/home/user/dio_videos/jornada-node") == "jornada-node"
    assert DioPlatform().extract_slug("jornada-node") == "jornada-node"


def test_dio_extract_slug_from_url():
    assert DioPlatform().extract_slug("https://web.dio.me/track/jornada-node") == "jornada-node"


def test_dio_matches():
    assert DioPlatform().matches_url("https://web.dio.me/track/x") is True


def test_alura_extract_slug():
    url = "https://cursos.alura.com.br/course/docker-fundamentos"
    assert AluraPlatform().extract_slug(url) == "docker-fundamentos"


def test_alura_matches():
    assert AluraPlatform().matches_url("https://cursos.alura.com.br/course/x") is True


def test_detect_platform_udemy():
    assert isinstance(detect_platform("https://udemy.com/course/x"), UdemyPlatform)


def test_detect_platform_alura():
    assert isinstance(detect_platform("https://cursos.alura.com.br/course/x"), AluraPlatform)


def test_detect_platform_dio():
    assert isinstance(detect_platform("https://web.dio.me/track/x"), DioPlatform)


def test_detect_platform_fallback_udemy():
    """Slug puro → fallback pra Udemy (comportamento v0.1 preservado)."""
    assert isinstance(detect_platform("slug-direto"), UdemyPlatform)


def test_get_platform_by_name():
    assert isinstance(get_platform("udemy"), UdemyPlatform)
    assert isinstance(get_platform("DIO"), DioPlatform)
    assert isinstance(get_platform("alura"), AluraPlatform)


def test_get_platform_unknown_raises():
    with pytest.raises(ValueError, match="não suportada"):
        get_platform("coursera")


def test_all_platforms_provide_info():
    for p in (UdemyPlatform(), DioPlatform(), AluraPlatform()):
        info = p.info()
        assert info.name
        assert info.base_url
        assert info.description


def test_base_platform_is_abstract():
    with pytest.raises(TypeError):
        BasePlatform()  # type: ignore[abstract]
