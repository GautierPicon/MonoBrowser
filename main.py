import re
import sys
from urllib.parse import quote
from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QToolBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from pathlib import Path

ICON_PATH = Path(__file__).parent / "icon.png"

KNOWN_SCHEMES = ("http://", "https://", "ftp://", "file://", "about:", "chrome://")


def is_likely_url(text):
    return (
        text.lower().startswith(KNOWN_SCHEMES)
        or re.search(r'\.[a-zA-Z]{2,}(:\d+)?(/|$)', text)
        or re.match(r'^[\w-]+\.[\w-]+', text)
        or text.startswith(("localhost", "127.", "10.", "192.168."))
        or re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text)
    )


class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MonoBrowser")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1200, 800)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.setCentralWidget(self.browser)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.url_bar)

        self.browser.urlChanged.connect(self.update_url_bar)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        if " " in text or not is_likely_url(text):
            url = QUrl(f"https://www.google.com/search?q={quote(text)}")
        else:
            if not text.lower().startswith(("http://", "https://", "ftp://", "file://")):
                text = "https://" + text
            url = QUrl(text)

        self.browser.setUrl(url)

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()