import base64
import platform
from functools import lru_cache
from html import escape
from urllib.parse import quote

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from monobrowser import utils
from monobrowser.utils import assets_path, get_version, resource_path

ABOUT_HTML_PATH = resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = resource_path("about-pages/settings.html")
ERROR_HTML_PATH = resource_path("about-pages/error.html")


def _common_css(effective: str) -> str:
    return f"""
  :root {{ color-scheme: {effective}; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{ background: #f5f5f7; color: #1d1d1f; }}
  h1 {{ color: #000000; }}

  .theme-dark body {{ background: #1c1c1e; color: #f5f5f7; }}
  .theme-dark h1 {{ color: #ffffff; }}
"""


def _effective_theme(theme: str) -> str:
    if theme in ("light", "dark"):
        return theme
    app = QGuiApplication.instance()
    if isinstance(app, QGuiApplication):
        hints = app.styleHints()
        if hints is not None and hints.colorScheme() == Qt.ColorScheme.Dark:
            return "dark"
    return "light"


def _theme_attr(effective: str) -> str:
    return ' class="theme-dark"' if effective == "dark" else ""


@lru_cache(maxsize=1)
def _icon_data_uri() -> str:
    b64 = base64.b64encode(assets_path("icons/icon.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


@lru_cache(maxsize=1)
def _globe_data_uri() -> str:
    return utils.icon_data_url("svg/globe.svg", "#86868b")


@lru_cache(maxsize=1)
def _mono_data_uri() -> str:
    svg = assets_path("svg/mono.svg").read_text(encoding="utf-8")
    svg = svg.replace('stroke="#000000"', 'stroke="#86868b"')
    encoded = base64.b64encode(svg.encode("utf-8")).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def _appearance_icon(name: str) -> str:
    return utils.icon_data_url(f"svg/appearance/{name}.svg", "#86868b")


def version_html(theme: str = "system") -> str:
    effective = _effective_theme(theme)
    return (
        ABOUT_HTML_PATH.read_text(encoding="utf-8")
        .replace("{{THEME_ATTR}}", _theme_attr(effective))
        .replace("{{COMMON_CSS}}", _common_css(effective))
        .replace("{{FAVICON}}", _mono_data_uri())
        .replace("{{ICON}}", _icon_data_uri())
        .replace("{{VERSION}}", get_version())
        .replace("{{ARCHITECTURE}}", platform.machine())
    )


def newtab_html(theme: str = "system") -> str:
    effective = _effective_theme(theme)
    return (
        NEWTAB_HTML_PATH.read_text(encoding="utf-8")
        .replace("{{THEME_ATTR}}", _theme_attr(effective))
        .replace("{{COMMON_CSS}}", _common_css(effective))
        .replace("{{FAVICON}}", _mono_data_uri())
    )


def settings_html(
    engine: str,
    restore: bool = True,
    theme: str = "system",
    adblock: bool = True,
    adblock_cosmetic: bool = False,
) -> str:
    from monobrowser import adblock as adblock_module

    effective = _effective_theme(theme)
    html = SETTINGS_HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("{{THEME_ATTR}}", _theme_attr(effective))
    html = html.replace("{{COMMON_CSS}}", _common_css(effective))
    html = html.replace("{{FAVICON}}", _mono_data_uri())
    html = html.replace("{{#google}}", " selected" if engine == "google" else "")
    html = html.replace(
        "{{#duckduckgo}}", " selected" if engine == "duckduckgo" else ""
    )
    html = html.replace("{{#restore}}", " selected" if restore else "")
    html = html.replace("{{#adblock}}", " on" if adblock else "")
    html = html.replace("{{ADBLOCK_ARIA}}", "true" if adblock else "false")
    html = html.replace("{{BLOCKED_COUNT}}", str(adblock_module.blocked_count()))
    if adblock:
        html = html.replace("{{COSMETIC_ROW_BEGIN}}", "")
        html = html.replace("{{COSMETIC_ROW_END}}", "")
    else:
        start = html.index("{{COSMETIC_ROW_BEGIN}}")
        end = html.index("{{COSMETIC_ROW_END}}") + len("{{COSMETIC_ROW_END}}")
        html = html[:start] + html[end:]
    html = html.replace("{{#cosmetic}}", " on" if adblock_cosmetic else "")
    html = html.replace("{{COSMETIC_ARIA}}", "true" if adblock_cosmetic else "false")
    count = len(adblock_module.blocked_domains())
    html = html.replace("{{ADBLOCK_COUNT}}", f"{count:,}".replace(",", " "))
    for mode in ("system", "light", "dark"):
        html = html.replace(f"{{{{#{mode}}}}}", " selected" if theme == mode else "")
    html = html.replace("{{ICON_SYSTEM}}", _appearance_icon("system"))
    html = html.replace("{{ICON_LIGHT}}", _appearance_icon("light"))
    html = html.replace("{{ICON_DARK}}", _appearance_icon("dark"))
    return html


def error_html(url: str, reason: str = "", theme: str = "system") -> str:
    effective = _effective_theme(theme)
    retry = utils.INTERNAL_RETRY_BASE + quote(url, safe="")
    return (
        ERROR_HTML_PATH.read_text(encoding="utf-8")
        .replace("{{THEME_ATTR}}", _theme_attr(effective))
        .replace("{{COMMON_CSS}}", _common_css(effective))
        .replace("{{FAVICON}}", _globe_data_uri())
        .replace("{{ICON}}", _globe_data_uri())
        .replace("{{URL}}", escape(url))
        .replace("{{REASON}}", escape(reason))
        .replace("{{RETRY}}", retry)
    )
