import base64
import platform

from monobrowser.utils import _assets_path, _resource_path, get_version

ABOUT_HTML_PATH = _resource_path("about-pages/version.html")
NEWTAB_HTML_PATH = _resource_path("about-pages/newtab.html")
SETTINGS_HTML_PATH = _resource_path("about-pages/settings.html")


def version_html() -> str:
    html_template = ABOUT_HTML_PATH.read_text(encoding="utf-8")
    icon_path = _assets_path("icon.png")
    b64 = base64.b64encode(icon_path.read_bytes()).decode()
    icon_data_uri = f"data:image/png;base64,{b64}"
    return (
        html_template.replace("{{ICON}}", icon_data_uri)
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
