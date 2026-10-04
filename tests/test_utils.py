from pathlib import Path

import pytest
from PyQt6.QtCore import QUrl

from monobrowser import utils
from monobrowser.utils import (
    build_url,
    get_version,
    internal_url_action,
    is_likely_url,
    resolve_address_text,
)


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


def test_resolve_address_text_url() -> None:
    assert resolve_address_text("example.com") == "https://example.com"
    assert resolve_address_text("http://example.com/a") == "http://example.com/a"


def test_resolve_address_text_search() -> None:
    assert (
        resolve_address_text("chat mignon") == "https://duckduckgo.com/?q=chat%20mignon"
    )
    assert resolve_address_text("chat mignon", "google").startswith(
        "https://www.google.com/search?q="
    )


def test_resolve_address_text_unknown_engine_falls_back() -> None:
    assert resolve_address_text("hello world", "nope").startswith(
        "https://duckduckgo.com/"
    )


def test_internal_url_action_set_search() -> None:
    assert internal_url_action("https://monobrowser.internal/set-search?google") == (
        "set-search",
        "google",
    )
    assert internal_url_action("https://monobrowser.internal/set-search?nope") == (
        "",
        "",
    )


def test_internal_url_action_search() -> None:
    assert internal_url_action(
        "https://monobrowser.internal/search?q=hello%20world"
    ) == ("search", "hello world")


def test_internal_url_action_other() -> None:
    assert internal_url_action("https://example.com/") == ("", "")
