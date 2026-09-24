from urllib.parse import parse_qs, quote, urlsplit

from PyQt6.QtCore import QEvent, QTimer, QUrl
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from monobrowser.about_pages import render_about, render_newtab, render_settings
from monobrowser.tab_bar import TABSTRIP_BG, ChromeTabBar
from monobrowser.tab_page import TabPage
from monobrowser.utils import _assets_path, build_url, is_likely_url
from monobrowser.widgets import nav_button


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

        self.search_engines = {
            "google": "https://www.google.com/search?q={}",
            "duckduckgo": "https://duckduckgo.com/?q={}",
        }
        self.current_search_engine = "duckduckgo"

        self.setup_menu()
        self.setup_tab_bar(root)
        self.setup_url_bar(root)
        self.setup_progress(root)
        self.setup_content(root)
        self.setup_shortcuts()

        self.add_tab()
        self.update_nav_buttons()

    def setup_menu(self):
        file_menu = self.menuBar().addMenu("File")

        settings_action = QAction("Settings…", self)
        settings_action.setMenuRole(QAction.MenuRole.PreferencesRole)
        settings_action.triggered.connect(self.settings)
        file_menu.addAction(settings_action)

        about_action = QAction("About MonoBrowser", self)
        about_action.setMenuRole(QAction.MenuRole.AboutRole)
        about_action.triggered.connect(self.about)
        file_menu.addAction(about_action)

    def _connect_browser(self, view):
        view.urlChanged.connect(self.on_url_changed)
        view.titleChanged.connect(self.on_title_changed)
        view.iconChanged.connect(self.on_icon_changed)
        view.loadStarted.connect(self.on_load_started)
        view.loadProgress.connect(self.on_load_progress)
        view.loadFinished.connect(self.on_load_finished)

    def _tab_index_of(self, view) -> int:
        for i in range(self.stack.count()):
            if self.stack.widget(i).browser is view:
                return i
        return -1

    def _open_tab(self, title: str) -> TabPage:
        page = TabPage(new_window_callback=self.create_popup_tab)
        self._connect_browser(page.browser)
        self.stack.addWidget(page)
        index = self.tab_bar.addTab(title)
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)
        return page

    def about(self):
        page = self._open_tab("About")
        render_about(page.browser)
        self.url_bar.setText("about:version")

    def new_tab_page(self):
        page = self._open_tab("New Tab")
        render_newtab(page.browser)
        QTimer.singleShot(
            0,
            lambda: (
                self.url_bar.clear(),
                self.url_bar.setFocus(),
            ),
        )

    def settings(self):
        page = self._open_tab("Settings")
        render_settings(page.browser, self.current_search_engine)
        self.url_bar.setText("about:settings")

    def setup_tab_bar(self, root):
        row = QWidget()
        row.setStyleSheet(f"background: {TABSTRIP_BG.name()};")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.setSpacing(4)

        self.tab_bar = ChromeTabBar()
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_bar)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setFixedSize(28, 28)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.setStyleSheet(
            "QPushButton { border: none; border-radius: 14px; font-size: 16px; }"
            "QPushButton:hover { background: #c7cbd1; }"
        )
        new_tab_btn.clicked.connect(lambda: self.add_tab())
        layout.addWidget(new_tab_btn)

        layout.addStretch(1)
        root.addWidget(row)

    def setup_url_bar(self, root):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        row.setStyleSheet(
            "QLineEdit { border: 1px solid palette(mid); border-radius: 8px;"
            " padding: 4px 10px; }"
            "QLineEdit:focus { border-color: #5b8def; }"
            "QPushButton { border: none; border-radius: 6px; }"
            "QPushButton:hover { background: palette(midlight); }"
        )

        self.back_btn = nav_button("back.svg", "←", "Back")
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)

        self.forward_btn = nav_button("forward.svg", "→", "Forward")
        self.forward_btn.clicked.connect(self.go_forward)
        layout.addWidget(self.forward_btn)

        self.reload_btn = nav_button("reload.svg", "⟳", "Reload")
        self.reload_btn.clicked.connect(self.reload_or_stop)
        layout.addWidget(self.reload_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.installEventFilter(self)
        layout.addWidget(self.url_bar, 1)

        root.addWidget(row)

    def eventFilter(self, obj, event):
        if obj is self.url_bar and event.type() == QEvent.Type.MouseButtonPress:
            QTimer.singleShot(0, self.url_bar.selectAll)
        return super().eventFilter(obj, event)

    def setup_progress(self, root):
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet(
            "QProgressBar { border: none; background: transparent; }"
            "QProgressBar::chunk { background: #5b8def; }"
        )
        self.progress.hide()
        root.addWidget(self.progress)

    def setup_content(self, root):
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

    def setup_shortcuts(self):
        bindings = [
            ("Ctrl+T", self.add_tab),
            ("Ctrl+L", self.focus_url_bar),
            ("Ctrl+W", self.close_current_tab),
            ("Ctrl+R", self.reload_current),
            ("Escape", self.stop_current),
        ]
        for sequence, slot in bindings:
            QShortcut(QKeySequence(sequence), self).activated.connect(slot)
        for i in range(8):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda index=i: self.go_to_tab(index))
        last_tab = QShortcut(QKeySequence("Ctrl+9"), self)
        last_tab.activated.connect(self.go_to_last_tab)

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def close_current_tab(self):
        self.close_tab(self.tab_bar.currentIndex())

    def reload_current(self):
        browser = self.current_browser()
        if browser:
            browser.reload()

    def stop_current(self):
        browser = self.current_browser()
        if browser:
            browser.stop()

    def go_to_tab(self, index: int):
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(index)

    def go_to_last_tab(self):
        count = self.tab_bar.count()
        if count > 0:
            self.tab_bar.setCurrentIndex(count - 1)

    def add_tab(self, url=None):
        if url is None:
            self.new_tab_page()
            return
        page = self._open_tab("New Tab")
        page.browser.setUrl(url)

    def create_popup_tab(self) -> QWebEnginePage:
        page = self._open_tab("New Tab")
        new_page = page.browser.page()
        assert new_page is not None
        return new_page

    def current_browser(self):
        page = self.stack.currentWidget()
        if page:
            return page.browser
        return None

    def go_back(self):
        browser = self.current_browser()
        if browser:
            browser.back()

    def go_forward(self):
        browser = self.current_browser()
        if browser:
            browser.forward()

    def reload_or_stop(self):
        browser = self.current_browser()
        if not browser:
            return
        if self.progress.isVisible():
            browser.stop()
        else:
            browser.reload()

    def _set_stop_mode(self, loading: bool):
        if loading:
            self.reload_btn.setIcon(QIcon())
            self.reload_btn.setText("✕")
            self.reload_btn.setToolTip("Stop")
        else:
            reload_path = _assets_path("reload.svg")
            if reload_path.exists():
                self.reload_btn.setIcon(QIcon(str(reload_path)))
                self.reload_btn.setText("")
            else:
                self.reload_btn.setIcon(QIcon())
                self.reload_btn.setText("⟳")
            self.reload_btn.setToolTip("Reload")

    def update_nav_buttons(self):
        browser = self.current_browser()
        if browser:
            history = browser.history()
            self.back_btn.setEnabled(history.canGoBack())
            self.forward_btn.setEnabled(history.canGoForward())
            self.reload_btn.setEnabled(True)
        else:
            self.back_btn.setEnabled(False)
            self.forward_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)

    def close_tab(self, index):
        if self.tab_bar.count() <= 1:
            return
        page = self.stack.widget(index)
        self.stack.removeWidget(page)
        self.tab_bar.removeTab(index)
        page.deleteLater()

    def on_tab_changed(self, index):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
        browser = self.current_browser()
        if browser:
            url = browser.url().toString()
            if url == "about:newtab":
                self.url_bar.clear()
            else:
                self.url_bar.setText(url)
        self.progress.hide()
        self._set_stop_mode(False)
        self.update_nav_buttons()

    def on_url_changed(self, qurl):
        url_str = qurl.toString()
        if url_str.startswith("https://monobrowser.internal/set-search?"):
            _, _, name = url_str.partition("?")
            if name in self.search_engines:
                self.current_search_engine = name
                render_settings(self.sender(), name)
            return

        if url_str.startswith("https://monobrowser.internal/search?"):
            query = parse_qs(urlsplit(url_str).query).get("q", [""])[0].strip()
            view = self.sender()
            if isinstance(view, QWebEngineView):
                if query:
                    view.setUrl(self.resolve_address(query))
                else:
                    render_newtab(view)
            return

        if self.sender() is self.current_browser():
            if url_str == "about:newtab":
                self.url_bar.clear()
            else:
                self.url_bar.setText(url_str)
            if self.url_bar.hasFocus():
                self.url_bar.selectAll()
            self.update_nav_buttons()

    def on_icon_changed(self, icon: QIcon):
        index = self._tab_index_of(self.sender())
        if index >= 0:
            self.tab_bar.setTabIcon(index, icon)

    def on_load_started(self):
        index = self._tab_index_of(self.sender())
        if index >= 0:
            self.tab_bar.setTabIcon(index, QIcon())
        if self.sender() is self.current_browser():
            self.progress.setValue(0)
            self.progress.show()
            self._set_stop_mode(True)

    def on_load_progress(self, value: int):
        if self.sender() is self.current_browser():
            self.progress.setValue(value)

    def on_load_finished(self, ok: bool):
        if self.sender() is self.current_browser():
            self.progress.hide()
            self._set_stop_mode(False)

    def on_title_changed(self, title):
        index = self._tab_index_of(self.sender())
        if index >= 0:
            self.tab_bar.setTabText(index, title or "New Tab")

    def resolve_address(self, text: str) -> QUrl:
        if " " in text or not is_likely_url(text):
            return QUrl(
                self.search_engines[self.current_search_engine].format(quote(text))
            )
        return build_url(text)

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

        if text == "about:settings":
            self.settings()
            return

        browser.setUrl(self.resolve_address(text))
