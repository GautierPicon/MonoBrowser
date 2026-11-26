import base64
import hashlib
import platform
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from monobrowser import utils
from monobrowser.utils import assets_path, get_version, resource_path

ABOUT_HTML_PATH = resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = resource_path("about-pages/settings.html")
HISTORY_HTML_PATH = resource_path("about-pages/history.html")
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


@lru_cache(maxsize=2)
def _search_engine_icon(name: str) -> str:
    data = assets_path(f"searchEngine/{name}.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()


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
    antitrack: bool = True,
    suggestions: bool = True,
    cosmetic_rules: bool = False,
) -> str:
    from monobrowser import adblock as adblock_module

    effective = _effective_theme(theme)
    subs: dict[str, str] = {
        "THEME_ATTR": _theme_attr(effective),
        "COMMON_CSS": _common_css(effective),
        "FAVICON": _mono_data_uri(),
        "#google": " selected" if engine == "google" else "",
        "#duckduckgo": " selected" if engine == "duckduckgo" else "",
        "GOOGLE_ARIA": "true" if engine == "google" else "false",
        "DUCKDUCKGO_ARIA": "true" if engine == "duckduckgo" else "false",
        "#restore": " on" if restore else "",
        "RESTORE_ARIA": "true" if restore else "false",
        "#adblock": " on" if adblock else "",
        "ADBLOCK_ARIA": "true" if adblock else "false",
        "BLOCKED_COUNT": str(adblock_module.blocked_count()),
        "#cosmetic": " on" if adblock_cosmetic else "",
        "COSMETIC_ARIA": "true" if adblock_cosmetic else "false",
        "#cosmetic_rules": " on" if cosmetic_rules else "",
        "COSMETIC_RULES_ARIA": "true" if cosmetic_rules else "false",
        "#antitrack": " on" if antitrack else "",
        "ANTITRACK_ARIA": "true" if antitrack else "false",
        "#suggestions": " on" if suggestions else "",
        "SUGGESTIONS_ARIA": "true" if suggestions else "false",
        "ADBLOCK_COUNT": f"{len(adblock_module.blocked_domains()):,}".replace(",", " "),
        "ICON_SYSTEM": _appearance_icon("system"),
        "ICON_LIGHT": _appearance_icon("light"),
        "ICON_DARK": _appearance_icon("dark"),
        "ICON_GOOGLE": _search_engine_icon("google"),
        "ICON_DUCKDUCKGO": _search_engine_icon("duckduckgo"),
    }
    for mode in ("system", "light", "dark"):
        subs[f"#{mode}"] = " selected" if theme == mode else ""
        subs[f"{mode.upper()}_ARIA"] = "true" if theme == mode else "false"
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


def _history_rows(items: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for item in items:
        url = str(item.get("url", ""))
        title = str(item.get("title", "")) or url
        icon = str(item.get("icon", "") or "")
        entry_id = str(item.get("id", "") or "")
        ts = item.get("ts")
        when = ""
        if isinstance(ts, (int, float)) and not isinstance(ts, bool) and ts > 0:
            when = datetime.fromtimestamp(ts).strftime("%d %b %Y · %H:%M")
        hue = int(hashlib.md5(url.encode("utf-8")).hexdigest(), 16) % 360
        letter = escape((title.strip() or url)[:1].upper())
        search = escape(f"{title} {url}".lower(), quote=True)
        style = f"background:hsl({hue},55%,55%)"
        monogram = f'<span class="monogram" style="{style}">{letter}</span>'
        icon_html = ""
        if icon:
            icon_html = (
                f'<img class="favicon" src="{escape(icon, quote=True)}"'
                f' loading="lazy" alt="" onerror="this.remove()">'
            )
        remove_url = utils.INTERNAL_REMOVE_HISTORY_BASE + quote(entry_id, safe="")
        rows.append(
            f'<div class="entry" data-search="{search}">'
            f'<a class="entry-link" href="{escape(url, quote=True)}">'
            f'<span class="icon-wrap">{monogram}{icon_html}</span>'
            f'<span class="meta"><span class="title">{escape(title)}</span>'
            f'<span class="url">{escape(url)}</span></span>'
            f'<span class="time">{escape(when)}</span>'
            f"</a>"
            f'<a class="remove" href="{escape(remove_url, quote=True)}"'
            f' title="Remove from history" aria-label="Remove from history">×</a>'
            f"</div>"
        )
    return "\n".join(rows)


def history_html(theme: str = "system") -> str:
    from monobrowser import history

    effective = _effective_theme(theme)
    items = history.entries()
    count = len(items)
    return _render(
        HISTORY_HTML_PATH,
        THEME_ATTR=_theme_attr(effective),
        COMMON_CSS=_common_css(effective),
        FAVICON=_mono_data_uri(),
        COUNT=f"{count} {'entry' if count == 1 else 'entries'}",
        ROWS=_history_rows(items),
        EMPTY_HIDDEN="hidden" if count else "",
        CLEAR_HIDDEN="" if count else "hidden",
    )


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
