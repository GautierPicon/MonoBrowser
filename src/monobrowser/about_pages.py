import base64
import platform
from functools import lru_cache

from monobrowser.utils import assets_path, get_version, resource_path

ABOUT_HTML_PATH = resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = resource_path("about-pages/settings.html")


@lru_cache(maxsize=1)
def _icon_data_uri() -> str:
    b64 = base64.b64encode(assets_path("icon.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


def version_html() -> str:
    html_template = ABOUT_HTML_PATH.read_text(encoding="utf-8")
    return (
        html_template.replace("{{ICON}}", _icon_data_uri())
        .replace("{{VERSION}}", get_version())
        .replace("{{ARCHITECTURE}}", platform.machine())
    )


def newtab_html() -> str:
    return NEWTAB_HTML_PATH.read_text(encoding="utf-8")


def settings_html(engine: str) -> str:
    html = SETTINGS_HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("{{#google}}", " selected" if engine == "google" else "")
    html = html.replace(
        "{{#duckduckgo}}", " selected" if engine == "duckduckgo" else ""
    )
    return html
