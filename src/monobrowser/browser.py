from urllib.parse import quote

from PyQt6.QtCore import QEvent, QTimer, QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from about_pages import render_about, render_newtab, render_settings
from tab_page import TabPage
from utils import build_url, is_likely_url


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
        self.current_search_engine = "google"

        self.setup_menu()
        self.setup_tab_bar(root)
        self.setup_url_bar(root)
        self.setup_content(root)

        self.add_tab()

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

    def about(self):
        page = TabPage()
        self.stack.addWidget(page)
        index = self.tab_bar.addTab("About")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)
        page.browser.urlChanged.connect(self.on_url_changed)
        render_about(page.browser)
        self.url_bar.setText("about:version")
        self.tab_bar.setTabText(index, "About")

    def new_tab_page(self):
        page = TabPage()
        self.stack.addWidget(page)
        index = self.tab_bar.addTab("New Tab")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)
        page.browser.urlChanged.connect(self.on_url_changed)
        page.browser.titleChanged.connect(self.on_title_changed)
        render_newtab(page.browser)
        self.tab_bar.setTabText(index, "New Tab")
        QTimer.singleShot(0, lambda: (
            self.url_bar.setText("about:newtab"),
            self.url_bar.setFocus(),
            self.url_bar.selectAll(),
        ))

    def settings(self):
        page = TabPage()
        self.stack.addWidget(page)
        index = self.tab_bar.addTab("Settings")
        self.tab_bar.setCurrentIndex(index)
        self.stack.setCurrentWidget(page)
        browser = page.browser
        browser.urlChanged.connect(self.on_url_changed)
        browser.titleChanged.connect(self.on_title_changed)
        render_settings(browser, self.current_search_engine)
        self.url_bar.setText("about:settings")
        self.tab_bar.setTabText(index, "Settings")

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
        url_str = qurl.toString()
        if url_str.startswith("https://monobrowser.internal/set-search?"):
            name = url_str.split("?")[1]
            if name in self.search_engines:
                self.current_search_engine = name
                render_settings(self.sender(), name)
            return

        if self.sender() is self.current_browser():
            self.url_bar.setText(url_str)
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

        if text == "about:settings":
            self.settings()
            return

        if " " in text or not is_likely_url(text):
            url = QUrl(self.search_engines[self.current_search_engine].format(quote(text)))
        else:
            url = build_url(text)

        browser.setUrl(url)
