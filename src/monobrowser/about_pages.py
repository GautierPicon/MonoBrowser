import base64
import platform
from functools import lru_cache
from html import escape
from urllib.parse import quote

from monobrowser import utils
from monobrowser.utils import assets_path, get_version, resource_path

ABOUT_HTML_PATH = resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = resource_path("about-pages/settings.html")
ERROR_HTML_PATH = resource_path("about-pages/error.html")

COMMON_CSS = """
  :root { color-scheme: light dark; }
  * { margin: 0; padding: 0; box-sizing: border-box; }

  @media (prefers-color-scheme: dark) {
    body { background: #1c1c1e; color: #f5f5f7; }
    h1 { color: #ffffff; }
  }
"""


@lru_cache(maxsize=1)
def _icon_data_uri() -> str:
    b64 = base64.b64encode(assets_path("icon.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


@lru_cache(maxsize=1)
def _globe_data_uri() -> str:
    return utils.icon_data_url("globe.svg", "#86868b")


def version_html() -> str:
    return (
        ABOUT_HTML_PATH.read_text(encoding="utf-8")
        .replace("{{COMMON_CSS}}", COMMON_CSS)
        .replace("{{ICON}}", _icon_data_uri())
        .replace("{{VERSION}}", get_version())
        .replace("{{ARCHITECTURE}}", platform.machine())
    )


def newtab_html() -> str:
    return NEWTAB_HTML_PATH.read_text(encoding="utf-8").replace(
        "{{COMMON_CSS}}", COMMON_CSS
    )


def settings_html(engine: str) -> str:
    html = SETTINGS_HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("{{COMMON_CSS}}", COMMON_CSS)
    html = html.replace("{{#google}}", " selected" if engine == "google" else "")
    html = html.replace(
        "{{#duckduckgo}}", " selected" if engine == "duckduckgo" else ""
    )
    return html


def error_html(url: str, reason: str = "") -> str:
    retry = utils.INTERNAL_RETRY_BASE + quote(url, safe="")
    return (
        ERROR_HTML_PATH.read_text(encoding="utf-8")
        .replace("{{COMMON_CSS}}", COMMON_CSS)
        .replace("{{ICON}}", _globe_data_uri())
        .replace("{{URL}}", escape(url))
        .replace("{{REASON}}", escape(reason))
        .replace("{{RETRY}}", retry)
    )
