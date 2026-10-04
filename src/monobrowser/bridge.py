"""Python <-> QML bridge: exposes headless-safe helpers to the QML layer."""

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from monobrowser import utils
from monobrowser.about_pages import newtab_html, settings_html, version_html

Property = getattr(QtCore, "pyqtProperty")


class Bridge(QObject):
    searchEngineChanged = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._search_engine = utils.DEFAULT_SEARCH_ENGINE

    @Property(str, notify=searchEngineChanged)
    def searchEngine(self) -> str:
        return self._search_engine

    @searchEngine.setter  # type: ignore[no-redef]
    def searchEngine(self, name: str) -> None:
        if name in utils.SEARCH_ENGINES and name != self._search_engine:
            self._search_engine = name
            self.searchEngineChanged.emit()

    @Property(str)
    def version(self) -> str:
        return utils.get_version()

    @pyqtSlot(str, result="QString")
    def resolveAddress(self, text: str) -> str:
        return utils.resolve_address_text(text, self._search_engine)

    @pyqtSlot(str, result="QString")
    def internalAction(self, url: str) -> str:
        return utils.internal_url_action(url)[0]

    @pyqtSlot(str, result="QString")
    def internalParam(self, url: str) -> str:
        return utils.internal_url_action(url)[1]

    @pyqtSlot(result="QString")
    def newtabHtml(self) -> str:
        return newtab_html()

    @pyqtSlot(result="QString")
    def settingsHtml(self) -> str:
        return settings_html(self._search_engine)

    @pyqtSlot(result="QString")
    def aboutHtml(self) -> str:
        return version_html()
