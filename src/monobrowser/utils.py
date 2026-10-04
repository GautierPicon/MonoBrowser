import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from PyQt6.QtCore import QUrl


def _is_bundled() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _resource_path(name: str) -> Path:
    if _is_bundled():
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).parent / name


def _assets_path(name: str) -> Path:
    if _is_bundled():
        return Path(getattr(sys, "_MEIPASS")) / name
    return Path(__file__).parent.parent / "assets" / name


def _project_root() -> Path:
    if _is_bundled():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).parent.parent.parent


def qml_path(name: str) -> Path:
    if _is_bundled():
        return Path(getattr(sys, "_MEIPASS")) / "qml" / name
    return Path(__file__).parent / "qml" / name


ICON_PATH = _assets_path("icon.icns")
if not ICON_PATH.exists():
    ICON_PATH = _assets_path("icon.png")
TOML_PATH = _project_root() / "pyproject.toml"

KNOWN_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:", "chrome://")
URL_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:")


def is_likely_url(text: str) -> bool:
    return bool(
        text.lower().startswith(KNOWN_SCHEMES)
        or re.search(r"\.[a-zA-Z]{2,}(:\d+)?(/|$)", text)
        or re.match(r"^[\w-]+\.[\w-]+", text)
        or text.startswith(("localhost", "127.", "10.", "192.168."))
        or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", text)
    )


def get_version() -> str:
    try:
        data = tomllib.loads(TOML_PATH.read_text())
        return data["project"]["version"]
    except Exception:
        return "0.0.0"


def build_url(text: str) -> QUrl:
    if not text.lower().startswith(URL_SCHEMES):
        text = "https://" + text
    return QUrl(text)


SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
}
DEFAULT_SEARCH_ENGINE = "duckduckgo"

INTERNAL_SEARCH_BASE = "https://monobrowser.internal/search?"
INTERNAL_SET_SEARCH_BASE = "https://monobrowser.internal/set-search?"


def resolve_address_text(text: str, engine: str = DEFAULT_SEARCH_ENGINE) -> str:
    text = text.strip()
    if " " in text or not is_likely_url(text):
        template = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_SEARCH_ENGINE])
        return template.format(quote(text))
    return build_url(text).toString()


def internal_url_action(url: str) -> tuple[str, str]:
    if url.startswith(INTERNAL_SET_SEARCH_BASE):
        _, _, name = url.partition("?")
        if name in SEARCH_ENGINES:
            return ("set-search", name)
        return ("", "")
    if url.startswith(INTERNAL_SEARCH_BASE):
        query = parse_qs(urlsplit(url).query).get("q", [""])[0].strip()
        return ("search", query)
    return ("", "")
