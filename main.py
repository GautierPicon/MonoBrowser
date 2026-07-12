import re
import sys
from pathlib import Path
from urllib.parse import quote

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
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

ICON_PATH = Path(__file__).parent / "icon.png"
DEFAULT_URL = "https://www.google.com"

KNOWN_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:", "chrome://")
URL_SCHEMES = ("http://", "https://", "ftp://", "file://")


def is_likely_url(text):
    return (
        text.lower().startswith(KNOWN_SCHEMES)
        or re.search(r'\.[a-zA-Z]{2,}(:\d+)?(/|$)', text)
        or re.match(r'^[\w-]+\.[\w-]+', text)
        or text.startswith(("localhost", "127.", "10.", "192.168."))
        or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text)
    )


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
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.setup_tab_bar(root)
        self.setup_url_bar(root)
        self.setup_content(root)

        self.add_tab()

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
        root.addWidget(self.url_bar)

    def setup_content(self, root):
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

    def add_tab(self, url=None):
        page = TabPage()
        page.browser.setUrl(url or QUrl(DEFAULT_URL))
        page.browser.urlChanged.connect(self.on_url_changed)

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
            index = self.tab_bar.currentIndex()
            title = qurl.host() or "New Tab"
            self.tab_bar.setTabText(index, title)

    def navigate_to_url(self):
        browser = self.current_browser()
        if not browser:
            return

        text = self.url_bar.text().strip()
        if not text:
            return

        if " " in text or not is_likely_url(text):
            url = build_search_url(text)
        else:
            url = build_url(text)

        browser.setUrl(url)


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
