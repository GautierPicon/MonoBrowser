import re
import sys
import tomllib
from pathlib import Path

from PyQt6.QtCore import QUrl


def _is_bundled():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def _resource_path(name):
    if _is_bundled():
        return Path(sys._MEIPASS) / name
    return Path(__file__).parent / name


ICON_PATH = _resource_path("icon.icns")
if not ICON_PATH.exists():
    ICON_PATH = _resource_path("icon.png")
TOML_PATH = _resource_path("pyproject.toml")

KNOWN_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:", "chrome://")
URL_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:")


def is_likely_url(text):
    return (
        text.lower().startswith(KNOWN_SCHEMES)
        or re.search(r'\.[a-zA-Z]{2,}(:\d+)?(/|$)', text)
        or re.match(r'^[\w-]+\.[\w-]+', text)
        or text.startswith(("localhost", "127.", "10.", "192.168."))
        or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text)
    )


def get_version():
    try:
        data = tomllib.loads(TOML_PATH.read_text())
        return data["project"]["version"]
    except Exception:
        return "0.0.0"


def build_url(text):
    if not text.lower().startswith(URL_SCHEMES):
        text = "https://" + text
    return QUrl(text)
