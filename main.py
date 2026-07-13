import base64
import platform
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import quote

from PyQt6.QtCore import Qt, QEvent, QTimer, QUrl
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

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
ABOUT_HTML_PATH = _resource_path("pages/version.html")
NEWTAB_HTML_PATH = _resource_path("pages/newtab.html")


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


def build_search_url(query):
    return QUrl(f"https://www.google.com/search?q={quote(query)}")


def build_url(text):
    if not text.lower().startswith(URL_SCHEMES):
        text = "https://" + text
    return QUrl(text)


class TabPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser = QWebEngineView()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)


class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonoBrowser")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.setup_menu()
        self.setup_tab_bar(root)
        self.setup_url_bar(root)
        self.setup_content(root)

        self.add_tab()

    def setup_menu(self):
        file_menu = self.menuBar().addMenu("File")
        about_action = QAction("About MonoBrowser", self)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self.about)
        file_menu.addAction(about_action)

    def about(self):
        page = TabPage()

        self.stack.addWidget(page)
        index = self.tab_bar.addTab("About")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)

        html_template = ABOUT_HTML_PATH.read_text(encoding="utf-8")

        icon_path = _resource_path("icon.png")
        b64 = base64.b64encode(icon_path.read_bytes()).decode()
        icon_data_uri = f"data:image/png;base64,{b64}"

        html = (html_template
                .replace("{{ICON}}", icon_data_uri)
                .replace("{{VERSION}}", get_version())
                .replace("{{ARCHITECTURE}}", platform.machine()))

        page.browser.urlChanged.connect(self.on_url_changed)
        page.browser.setHtml(html, QUrl("about:version"))
        self.url_bar.setText("about:version")
        self.tab_bar.setTabText(index, "About")

    def new_tab_page(self):
        page = TabPage()

        self.stack.addWidget(page)
        index = self.tab_bar.addTab("New Tab")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)

        html = NEWTAB_HTML_PATH.read_text(encoding="utf-8")

        page.browser.urlChanged.connect(self.on_url_changed)
        page.browser.titleChanged.connect(self.on_title_changed)
        page.browser.setHtml(html, QUrl("about:newtab"))
        self.tab_bar.setTabText(index, "New Tab")
        QTimer.singleShot(0, lambda: (
            self.url_bar.setText("about:newtab"),
            self.url_bar.setFocus(),
            self.url_bar.selectAll(),
        ))

    def setup_tab_bar(self, root):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_bar)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedWidth(30)
        new_tab_btn.clicked.connect(lambda: self.add_tab())
        layout.addWidget(new_tab_btn)

        layout.addStretch(1)

        root.addWidget(row)

    def setup_url_bar(self, root):
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.installEventFilter(self)
        root.addWidget(self.url_bar)

    def eventFilter(self, obj, event):
        if obj is self.url_bar and event.type() == QEvent.Type.MouseButtonPress:
            QTimer.singleShot(0, self.url_bar.selectAll)
        return super().eventFilter(obj, event)

    def setup_content(self, root):
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

    def add_tab(self, url=None):
        if url is None:
            self.new_tab_page()
            return
        page = TabPage()
        page.browser.setUrl(url)
        page.browser.urlChanged.connect(self.on_url_changed)
        page.browser.titleChanged.connect(self.on_title_changed)

        self.stack.addWidget(page)
        index = self.tab_bar.addTab("New Tab")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)

    def current_browser(self):
        page = self.stack.currentWidget()
        if page:
            return page.browser
        return None

    def close_tab(self, index):
        if self.tab_bar.count() <= 1:
            return
        page = self.stack.widget(index)
        self.stack.removeWidget(page)
        self.tab_bar.removeTab(index)

    def on_tab_changed(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
        browser = self.current_browser()
        if browser:
            self.url_bar.setText(browser.url().toString())

    def on_url_changed(self, qurl):
        if self.sender() is self.current_browser():
            self.url_bar.setText(qurl.toString())
            if self.url_bar.hasFocus():
                self.url_bar.selectAll()

    def on_title_changed(self, title):
        if self.sender() is self.current_browser():
            index = self.tab_bar.currentIndex()
            self.tab_bar.setTabText(index, title or "New Tab")

    def navigate_to_url(self):
        browser = self.current_browser()
        if not browser:
            return

        text = self.url_bar.text().strip()
        if not text:
            return

        if text == "about:version":
            self.about()
            return

        if text == "about:newtab":
            self.new_tab_page()
            return

        if " " in text or not is_likely_url(text):
            url = build_search_url(text)
        else:
            url = build_url(text)

        browser.setUrl(url)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MonoBrowser")
    app.setApplicationVersion(get_version())
    if not _is_bundled():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
