from collections.abc import Callable

from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class BrowserPage(QWebEnginePage):
    """Page that opens new windows (target=_blank, window.open) in a new tab.

    The default createWindow() does nothing, so popup links die silently.
    The browser injects a window_factory that creates a tab and returns its page.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.window_factory: Callable[[], QWebEnginePage] | None = None

    def createWindow(self, window_type: QWebEnginePage.WebWindowType) -> QWebEnginePage:
        # All popups (tabs and dialogs) open in a new browser tab.
        if self.window_factory is not None:
            return self.window_factory()
        return BrowserPage()


class TabPage(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        new_window_callback: Callable[[], QWebEnginePage] | None = None,
    ) -> None:
        super().__init__(parent)
        self.browser = QWebEngineView()
        page = BrowserPage(self.browser)
        page.window_factory = new_window_callback
        self.browser.setPage(page)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
