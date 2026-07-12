import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QToolBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mon Navigateur")
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
        url = self.url_bar.text().strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())


def main():
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()