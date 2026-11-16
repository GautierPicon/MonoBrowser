import base64
import tomllib
from pathlib import Path
from urllib.parse import quote

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


def test_build_url_keeps_chrome_scheme() -> None:
    assert build_url("chrome://settings").toString() == "chrome://settings"


def test_get_version_matches_pyproject() -> None:
    utils.get_version.cache_clear()
    data = tomllib.loads(utils.TOML_PATH.read_text())
    assert get_version() == data["project"]["version"]


def test_get_version_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(utils, "TOML_PATH", tmp_path / "missing.toml")
    utils.get_version.cache_clear()
    assert get_version() == "0.0.0"
    utils.get_version.cache_clear()


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


def test_internal_url_action_retry() -> None:
    target = "https://example.com/?a=b&c=d"
    encoded = quote(target, safe="")
    assert internal_url_action(f"https://monobrowser.internal/retry?url={encoded}") == (
        "retry",
        target,
    )
    assert internal_url_action("https://monobrowser.internal/retry?url=") == ("", "")


def test_icon_data_url_replaces_current_color() -> None:
    url = utils.icon_data_url("svg/lock/lock.svg", "#123456")
    assert url.startswith("data:image/svg+xml;base64,")
    svg = base64.b64decode(url.split(",", 1)[1]).decode()
    assert "#123456" in svg
    assert "currentColor" not in svg


def test_internal_url_action_set_theme() -> None:
    assert internal_url_action("https://monobrowser.internal/set-theme?light") == (
        "set-theme",
        "light",
    )
    assert internal_url_action("https://monobrowser.internal/set-theme?dark") == (
        "set-theme",
        "dark",
    )
    assert internal_url_action("https://monobrowser.internal/set-theme?system") == (
        "set-theme",
        "system",
    )
    assert internal_url_action("https://monobrowser.internal/set-theme?banana") == (
        "",
        "",
    )
    assert internal_url_action("https://monobrowser.internal/set-theme?") == ("", "")


def test_svg_favicon_data_uri_decodes() -> None:
    raw = (
        "image://favicon/data:image/svg+xml,"
        "%253Csvg xmlns='http://www.w3.org/2000/svg' width='73' height='63' "
        "viewBox='0 0 73 63' fill='none'%253E"
        "%253Cpath d='M36.5 0L28.2524Z' fill='%252300b898' /%253E%253C/svg%253E"
    )
    src = utils.svg_favicon_data_uri(raw)
    assert src is not None
    assert src.startswith("data:image/svg+xml;base64,")
    svg = base64.b64decode(src.split(",", 1)[1]).decode()
    assert "<svg" in svg
    assert "#00b898" in svg


def test_svg_favicon_data_uri_base64_passthrough() -> None:
    raw = "image://favicon/data:image/svg+xml;base64,PHN2Zy8+"
    assert utils.svg_favicon_data_uri(raw) == "data:image/svg+xml;base64,PHN2Zy8+"


def test_svg_favicon_data_uri_rejects_unmatched() -> None:
    assert utils.svg_favicon_data_uri("image://favicon/https://x/f.ico") is None
    assert utils.svg_favicon_data_uri("data:image/png;base64,PHN2Zy8+") is None
    assert utils.svg_favicon_data_uri("") is None


def test_svg_favicon_data_uri_raw_link_href() -> None:
    raw = (
        "data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg'%3E"
        "%3Cpath fill='%2300b898'/%3E%3C/svg%3E"
    )
    src = utils.svg_favicon_data_uri(raw)
    assert src is not None
    assert src.startswith("data:image/svg+xml;base64,")
    svg = base64.b64decode(src.split(",", 1)[1]).decode()
    assert "<svg" in svg
    assert "#00b898" in svg
