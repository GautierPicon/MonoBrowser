import base64
import re
import sys
import tomllib
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, unquote_to_bytes, urlsplit

from PyQt6.QtCore import QStandardPaths, QUrl


def is_bundled() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", "."))


def _bundled_file(name: Path | str) -> Path:
    return (_bundle_root() / name).resolve()


def resource_path(name: str) -> Path:
    if is_bundled():
        return _bundled_file(name)
    return Path(__file__).parent / name


def assets_path(name: str) -> Path:
    if is_bundled():
        return _bundled_file(name)
    return Path(__file__).parent.parent / "assets" / name


def _project_root() -> Path:
    if is_bundled():
        return _bundle_root()
    return Path(__file__).parent.parent.parent


def qml_path(name: str) -> Path:
    if is_bundled():
        return _bundled_file(Path("qml") / name)
    return Path(__file__).parent / "qml" / name


@lru_cache(maxsize=64)
def icon_data_url(name: str, color: str) -> str:
    try:
        svg = assets_path(name).read_text(encoding="utf-8")
    except OSError:
        return ""
    svg = svg.replace("currentColor", color)
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


ICON_PATH = assets_path("icons/icon.icns")
if not ICON_PATH.exists():
    ICON_PATH = assets_path("icons/icon.png")
TOML_PATH = _project_root() / "pyproject.toml"

KNOWN_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:", "chrome://")


def is_likely_url(text: str) -> bool:
    return bool(
        text.lower().startswith(KNOWN_SCHEMES)
        or re.search(r"\.[a-zA-Z]{2,}(:\d+)?(/|$)", text)
        or re.match(r"^[\w-]+\.[\w-]+", text)
        or text.startswith(("localhost", "127.", "10.", "192.168."))
        or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", text)
    )


@lru_cache(maxsize=1)
def get_version() -> str:
    try:
        data = tomllib.loads(TOML_PATH.read_text())
        return data["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "0.0.0"


def build_url(text: str) -> QUrl:
    if not text.lower().startswith(KNOWN_SCHEMES):
        text = "https://" + text
    return QUrl(text)


SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
}
DEFAULT_SEARCH_ENGINE = "duckduckgo"

INTERNAL_SEARCH_BASE = "https://monobrowser.internal/search?"
INTERNAL_SET_SEARCH_BASE = "https://monobrowser.internal/set-search?"
INTERNAL_SET_RESTORE_BASE = "https://monobrowser.internal/set-restore?"
INTERNAL_SET_THEME_BASE = "https://monobrowser.internal/set-theme?"
INTERNAL_SET_ADBLOCK_BASE = "https://monobrowser.internal/set-adblock?"
INTERNAL_SET_ADBLOCK_COSMETIC_BASE = (
    "https://monobrowser.internal/set-adblock-cosmetic?"
)
INTERNAL_SET_ANTITRACK_BASE = "https://monobrowser.internal/set-antitrack?"
INTERNAL_CLEAR_HISTORY_BASE = "https://monobrowser.internal/clear-history?"
INTERNAL_REMOVE_HISTORY_BASE = "https://monobrowser.internal/remove-history?id="
INTERNAL_RETRY_BASE = "https://monobrowser.internal/retry?url="


_SVG_DATA_URI_CACHE_MAX = 512_000


def _svg_favicon_data_uri_cached(icon: str) -> str | None:
    marker = "data:image/svg+xml"
    body = (
        icon[len("image://favicon/") :] if icon.startswith("image://favicon/") else icon
    )
    if not body.startswith(marker):
        return None
    decoded = unquote(body)
    if decoded.startswith(marker + ";base64,"):
        b64 = decoded.split(",", 1)[1]
        try:
            base64.b64decode(b64, validate=True)
        except Exception:
            return None
        return "data:image/svg+xml;base64," + b64
    if not decoded.startswith(marker + ","):
        return None
    payload = decoded[len(marker + ",") :]
    svg = unquote_to_bytes(payload)
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


@lru_cache(maxsize=128)
def _svg_favicon_data_uri_small(icon: str) -> str | None:
    return _svg_favicon_data_uri_cached(icon)


def svg_favicon_data_uri(icon: str) -> str | None:
    if len(icon) > _SVG_DATA_URI_CACHE_MAX:
        return _svg_favicon_data_uri_cached(icon)
    return _svg_favicon_data_uri_small(icon)


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
    if url.startswith(INTERNAL_SET_RESTORE_BASE):
        if url.partition("?")[2].strip() == "toggle":
            return ("set-restore", "toggle")
        return ("", "")
    if url.startswith(INTERNAL_SET_THEME_BASE):
        mode = url.partition("?")[2].strip()
        if mode in ("system", "light", "dark"):
            return ("set-theme", mode)
        return ("", "")
    if url.startswith(INTERNAL_SET_ADBLOCK_BASE):
        if url.partition("?")[2].strip() == "toggle":
            return ("set-adblock", "toggle")
        return ("", "")
    if url.startswith(INTERNAL_SET_ADBLOCK_COSMETIC_BASE):
        if url.partition("?")[2].strip() == "toggle":
            return ("set-adblock-cosmetic", "toggle")
        return ("", "")
    if url.startswith(INTERNAL_SET_ANTITRACK_BASE):
        if url.partition("?")[2].strip() == "toggle":
            return ("set-antitrack", "toggle")
        return ("", "")
    if url.startswith(INTERNAL_CLEAR_HISTORY_BASE):
        return ("clear-history", "")
    if url.startswith(INTERNAL_REMOVE_HISTORY_BASE):
        entry_id = parse_qs(urlsplit(url).query).get("id", [""])[0].strip()
        if entry_id:
            return ("remove-history", entry_id)
        return ("", "")
    if url.startswith(INTERNAL_SEARCH_BASE):
        query = parse_qs(urlsplit(url).query).get("q", [""])[0].strip()
        return ("search", query)
    if url.startswith(INTERNAL_RETRY_BASE):
        target = parse_qs(urlsplit(url).query).get("url", [""])[0].strip()
        if target:
            return ("retry", target)
        return ("", "")
    return ("", "")


def download_directory() -> Path:
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DownloadLocation
    )
    directory = Path(location) if location else Path.home() / "Downloads"
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path.home()
    return directory


def unique_download_path(directory: Path, filename: str) -> Path:
    name = Path(filename.replace("\\", "/")).name.strip()
    if not name or name in (".", ".."):
        name = "download"
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem = Path(name).stem
    suffix = Path(name).suffix
    index = 1
    while True:
        candidate = directory / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1
