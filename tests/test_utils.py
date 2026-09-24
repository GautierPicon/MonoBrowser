from pathlib import Path

import pytest
from PyQt6.QtCore import QUrl

from monobrowser import utils
from monobrowser.utils import build_url, get_version, is_likely_url


@pytest.mark.parametrize(
    "text",
    [
        "https://example.com",
        "http://example.com/path?q=1",
        "google.com",
        "example.com/search?q=x",
        "localhost:8000",
        "127.0.0.1:5000",
        "192.168.1.1",
        "about:version",
        "ftp://files.example.com",
    ],
)
def test_is_likely_url_true(text: str) -> None:
    assert is_likely_url(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "bonjour le monde",
        "quelle heure est-il",
        "chat mignon",
    ],
)
def test_is_likely_url_false(text: str) -> None:
    assert is_likely_url(text) is False


def test_build_url_adds_https() -> None:
    url = build_url("example.com")
    assert isinstance(url, QUrl)
    assert url.toString() == "https://example.com"


def test_build_url_keeps_scheme() -> None:
    assert build_url("http://example.com").toString() == "http://example.com"


def test_get_version_matches_pyproject() -> None:
    assert get_version() == "1.2.0"


def test_get_version_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(utils, "TOML_PATH", tmp_path / "missing.toml")
    assert get_version() == "0.0.0"
