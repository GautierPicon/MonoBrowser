import base64
import platform
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import quote

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from monobrowser import utils
from monobrowser.utils import assets_path, get_version, resource_path

ABOUT_HTML_PATH = resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = resource_path("about-pages/settings.html")
ERROR_HTML_PATH = resource_path("about-pages/error.html")


@lru_cache(maxsize=4)
def _read_about(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render(path: Path, **subs: str) -> str:
    html = _read_about(path)
    for key, value in subs.items():
        html = html.replace("{{" + key + "}}", value)
    return html


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
    return _render(
        ABOUT_HTML_PATH,
        THEME_ATTR=_theme_attr(effective),
        COMMON_CSS=_common_css(effective),
        FAVICON=_mono_data_uri(),
        ICON=_icon_data_uri(),
        VERSION=get_version(),
        ARCHITECTURE=platform.machine(),
    )


def newtab_html(theme: str = "system") -> str:
    effective = _effective_theme(theme)
    return _render(
        NEWTAB_HTML_PATH,
        THEME_ATTR=_theme_attr(effective),
        COMMON_CSS=_common_css(effective),
        FAVICON=_mono_data_uri(),
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
    subs: dict[str, str] = {
        "THEME_ATTR": _theme_attr(effective),
        "COMMON_CSS": _common_css(effective),
        "FAVICON": _mono_data_uri(),
        "#google": " selected" if engine == "google" else "",
        "#duckduckgo": " selected" if engine == "duckduckgo" else "",
        "#restore": " selected" if restore else "",
        "#adblock": " on" if adblock else "",
        "ADBLOCK_ARIA": "true" if adblock else "false",
        "BLOCKED_COUNT": str(adblock_module.blocked_count()),
        "#cosmetic": " on" if adblock_cosmetic else "",
        "COSMETIC_ARIA": "true" if adblock_cosmetic else "false",
        "ADBLOCK_COUNT": f"{len(adblock_module.blocked_domains()):,}".replace(",", " "),
        "ICON_SYSTEM": _appearance_icon("system"),
        "ICON_LIGHT": _appearance_icon("light"),
        "ICON_DARK": _appearance_icon("dark"),
    }
    for mode in ("system", "light", "dark"):
        subs[f"#{mode}"] = " selected" if theme == mode else ""
    if adblock:
        subs["COSMETIC_ROW_BEGIN"] = ""
        subs["COSMETIC_ROW_END"] = ""
        return _render(SETTINGS_HTML_PATH, **subs)
    html = _read_about(SETTINGS_HTML_PATH)
    start = html.find("{{COSMETIC_ROW_BEGIN}}")
    end = html.find("{{COSMETIC_ROW_END}}")
    if start != -1 and end != -1:
        html = html[:start] + html[end + len("{{COSMETIC_ROW_END}}") :]
    for key, value in subs.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def error_html(url: str, reason: str = "", theme: str = "system") -> str:
    effective = _effective_theme(theme)
    retry = utils.INTERNAL_RETRY_BASE + quote(url, safe="")
    return _render(
        ERROR_HTML_PATH,
        THEME_ATTR=_theme_attr(effective),
        COMMON_CSS=_common_css(effective),
        FAVICON=_globe_data_uri(),
        ICON=_globe_data_uri(),
        URL=escape(url),
        REASON=escape(reason),
        RETRY=retry,
    )
