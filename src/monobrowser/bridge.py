"""Python <-> QML bridge: exposes headless-safe helpers to the QML layer."""

from typing import Any

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from monobrowser import session, utils
from monobrowser.about_pages import error_html, newtab_html, settings_html, version_html

pyqtProperty = getattr(QtCore, "pyqtProperty")


class Bridge(QObject):
    searchEngineChanged = pyqtSignal()
    restoreSessionChanged = pyqtSignal()
    themeModeChanged = pyqtSignal()
    adblockEnabledChanged = pyqtSignal()
    adblockCosmeticChanged = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._search_engine = utils.DEFAULT_SEARCH_ENGINE

    @pyqtProperty(str, notify=searchEngineChanged)
    def searchEngine(self) -> str:
        return self._search_engine

    @searchEngine.setter  # type: ignore[no-redef]
    def searchEngine(self, name: str) -> None:
        if name in utils.SEARCH_ENGINES and name != self._search_engine:
            self._search_engine = name
            self.searchEngineChanged.emit()

    @pyqtProperty(bool, notify=restoreSessionChanged)
    def restoreSession(self) -> bool:
        return session.restore_enabled()

    @restoreSession.setter  # type: ignore[no-redef]
    def restoreSession(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.restore_enabled():
            session.set_restore_enabled(enabled)
            self.restoreSessionChanged.emit()

    @pyqtProperty(str, notify=themeModeChanged)
    def themeMode(self) -> str:
        return session.theme_mode()

    @themeMode.setter  # type: ignore[no-redef]
    def themeMode(self, mode: str) -> None:
        mode = mode.strip().lower()
        if mode in session.THEME_MODES and mode != session.theme_mode():
            session.set_theme_mode(mode)
            self.themeModeChanged.emit()

    @pyqtProperty(bool, notify=adblockEnabledChanged)
    def adblockEnabled(self) -> bool:
        return session.adblock_enabled()

    @adblockEnabled.setter  # type: ignore[no-redef]
    def adblockEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.adblock_enabled():
            session.set_adblock_enabled(enabled)
            self.adblockEnabledChanged.emit()

    @pyqtProperty(bool, notify=adblockCosmeticChanged)
    def adblockCosmetic(self) -> bool:
        return session.adblock_cosmetic()

    @adblockCosmetic.setter  # type: ignore[no-redef]
    def adblockCosmetic(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.adblock_cosmetic():
            session.set_adblock_cosmetic(enabled)
            self.adblockCosmeticChanged.emit()

    @pyqtProperty(str)
    def version(self) -> str:
        return utils.get_version()

    @pyqtSlot(str, result="QString")
    def resolveAddress(self, text: str) -> str:
        return utils.resolve_address_text(text, self._search_engine)

    @pyqtSlot(str, str, result="QString")
    def iconUrl(self, name: str, color: str) -> str:
        return utils.icon_data_url(name, color)

    @pyqtSlot(str, result="QString")
    def internalAction(self, url: str) -> str:
        return utils.internal_url_action(url)[0]

    @pyqtSlot(str, result="QString")
    def internalParam(self, url: str) -> str:
        return utils.internal_url_action(url)[1]

    @pyqtSlot(str, str, result="QString")
    def errorHtml(self, url: str, reason: str) -> str:
        return error_html(url, reason, session.theme_mode())

    @pyqtSlot(result="QString")
    def newtabHtml(self) -> str:
        return newtab_html(session.theme_mode())

    @pyqtSlot(result="QString")
    def settingsHtml(self) -> str:
        return settings_html(
            self._search_engine,
            session.restore_enabled(),
            session.theme_mode(),
            session.adblock_enabled(),
            session.adblock_cosmetic(),
        )

    @pyqtSlot(result="QString")
    def versionHtml(self) -> str:
        return version_html(session.theme_mode())

    @pyqtSlot(result="QVariant")
    def loadSessionState(self) -> dict[str, Any]:
        return session.load_state() or {}

    @pyqtSlot("QVariantList", int, int, int, int, int, bool)
    def saveSession(
        self,
        urls: list[str],
        current_index: int,
        x: int,
        y: int,
        width: int,
        height: int,
        maximized: bool,
    ) -> None:
        session.save_state(urls, current_index, x, y, width, height, maximized)
