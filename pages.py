import base64
import platform

from PyQt6.QtCore import QUrl

from utils import _resource_path, get_version

ABOUT_HTML_PATH = _resource_path("pages/version.html")
NEWTAB_HTML_PATH = _resource_path("pages/newtab.html")
SETTINGS_HTML_PATH = _resource_path("pages/settings.html")


def render_about(browser):
    html_template = ABOUT_HTML_PATH.read_text(encoding="utf-8")
    icon_path = _resource_path("icon.png")
    b64 = base64.b64encode(icon_path.read_bytes()).decode()
    icon_data_uri = f"data:image/png;base64,{b64}"
    html = (html_template
            .replace("{{ICON}}", icon_data_uri)
            .replace("{{VERSION}}", get_version())
            .replace("{{ARCHITECTURE}}", platform.machine()))
    browser.setHtml(html, QUrl("about:version"))


def render_newtab(browser):
    html = NEWTAB_HTML_PATH.read_text(encoding="utf-8")
    browser.setHtml(html, QUrl("about:newtab"))


def render_settings(browser, engine):
    html = SETTINGS_HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("{{#google}}", " selected" if engine == "google" else "")
    html = html.replace("{{#duckduckgo}}", " selected" if engine == "duckduckgo" else "")
    browser.setHtml(html, QUrl("about:settings"))
