"""Python <-> QML bridge: exposes headless-safe helpers to the QML layer."""

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QObject, QProcess, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from monobrowser import adblock, history, session, suggestions, utils
from monobrowser.about_pages import (
    error_html,
    history_html,
    newtab_html,
    settings_html,
    version_html,
)

pyqtProperty = getattr(QtCore, "pyqtProperty")


class Bridge(QObject):
    searchEngineChanged = pyqtSignal()
    restoreSessionChanged = pyqtSignal()
    themeModeChanged = pyqtSignal()
    adblockEnabledChanged = pyqtSignal()
    adblockCosmeticChanged = pyqtSignal()
    cosmeticRulesEnabledChanged = pyqtSignal()
    antitrackEnabledChanged = pyqtSignal()
    suggestionsEnabledChanged = pyqtSignal()
    suggestionsReady = pyqtSignal(str, "QStringList")

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._search_engine = utils.DEFAULT_SEARCH_ENGINE
        self._suggestions_manager: QNetworkAccessManager | None = None
        self._suggestions_reply: QNetworkReply | None = None
        self._suggestions_timer = QTimer(self)
        self._suggestions_timer.setSingleShot(True)
        self._suggestions_timer.timeout.connect(self._abortSuggestions)
        self.searchEngineChanged.connect(self._abortSuggestions)

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

    @pyqtProperty(bool, notify=cosmeticRulesEnabledChanged)
    def cosmeticRulesEnabled(self) -> bool:
        return session.cosmetic_rules_enabled()

    @cosmeticRulesEnabled.setter  # type: ignore[no-redef]
    def cosmeticRulesEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.cosmetic_rules_enabled():
            session.set_cosmetic_rules_enabled(enabled)
            self.cosmeticRulesEnabledChanged.emit()

    @pyqtProperty(bool, notify=antitrackEnabledChanged)
    def antitrackEnabled(self) -> bool:
        return session.antitrack_enabled()

    @antitrackEnabled.setter  # type: ignore[no-redef]
    def antitrackEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.antitrack_enabled():
            session.set_antitrack_enabled(enabled)
            self.antitrackEnabledChanged.emit()

    @pyqtProperty(bool, notify=suggestionsEnabledChanged)
    def suggestionsEnabled(self) -> bool:
        return session.suggestions_enabled()

    @suggestionsEnabled.setter  # type: ignore[no-redef]
    def suggestionsEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled != session.suggestions_enabled():
            session.set_suggestions_enabled(enabled)
            self.suggestionsEnabledChanged.emit()

    @pyqtProperty(str)
    def version(self) -> str:
        return utils.get_version()

    @pyqtSlot(str, result="QString")
    def resolveAddress(self, text: str) -> str:
        return utils.resolve_address_text(text, self._search_engine)

    @pyqtSlot(str)
    def requestSuggestions(self, text: str) -> None:
        self._abortSuggestions()
        query = text.strip()
        if not session.suggestions_enabled() or not query:
            return
        url = suggestions.suggestion_url(self._search_engine, query)
        if url is None or utils.is_likely_url(query):
            return
        if self._suggestions_manager is None:
            self._suggestions_manager = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        reply = self._suggestions_manager.get(request)
        if reply is None:
            return
        self._suggestions_reply = reply
        reply.finished.connect(lambda: self._onSuggestionsFinished(reply, query))
        self._suggestions_timer.start(suggestions.TIMEOUT_MS)

    def _abortSuggestions(self) -> None:
        self._suggestions_timer.stop()
        reply = self._suggestions_reply
        self._suggestions_reply = None
        if reply is not None:
            reply.abort()

    def _onSuggestionsFinished(self, reply: QNetworkReply, query: str) -> None:
        if self._suggestions_reply is not reply:
            reply.deleteLater()
            return
        self._suggestions_timer.stop()
        self._suggestions_reply = None
        if reply.error() == QNetworkReply.NetworkError.OperationCanceledError:
            reply.deleteLater()
            return
        payload = reply.readAll().data().decode("utf-8", errors="ignore")
        failed = reply.error() != QNetworkReply.NetworkError.NoError
        reply.deleteLater()
        if failed:
            return
        self.suggestionsReady.emit(query, suggestions.parse_suggestions(payload))

    @pyqtSlot(str, result="QString")
    def cosmeticCss(self, url: str) -> str:
        return adblock.cosmetic_selectors(url)

    @pyqtSlot(str, result="bool")
    def isExternalUrl(self, url: str) -> bool:
        return utils.is_external_url(url)

    @pyqtSlot(str, str, result="QString")
    def iconUrl(self, name: str, color: str) -> str:
        return utils.icon_data_url(name, color)

    @pyqtSlot(str, result="QString")
    def faviconSource(self, icon: str) -> str:
        return utils.svg_favicon_data_uri(icon) or icon

    @pyqtSlot(str, result="QVariantList")
    def internalRoute(self, url: str) -> list[str]:
        action, param = utils.internal_url_action(url)
        return [action, param]

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
            antitrack=session.antitrack_enabled(),
            suggestions=session.suggestions_enabled(),
            cosmetic_rules=session.cosmetic_rules_enabled(),
        )

    @pyqtSlot(result="QString")
    def versionHtml(self) -> str:
        return version_html(session.theme_mode())

    @pyqtSlot(result="QString")
    def historyHtml(self) -> str:
        return history_html(session.theme_mode())

    @pyqtSlot(str, str, str)
    def recordHistory(self, url: str, title: str = "", icon: str = "") -> None:
        history.record(url, title, icon)

    @pyqtSlot(str, int, result="QVariantList")
    def suggestMatches(self, text: str, limit: int) -> list[dict[str, Any]]:
        return history.suggest(text, limit)

    @pyqtSlot(str)
    def removeHistoryEntry(self, entry_id: str) -> None:
        history.remove(entry_id)

    @pyqtSlot()
    def clearHistory(self) -> None:
        history.clear()

    @pyqtSlot(str, str, result="QVariantList")
    def downloadDestination(self, suggested_name: str, url: str) -> list[str]:
        name = suggested_name.strip() or Path(urlsplit(url).path).name
        destination = utils.unique_download_path(utils.download_directory(), name)
        return [str(destination.parent), destination.name]

    @pyqtSlot(str)
    def revealDownload(self, path: str) -> None:
        if path.strip():
            QProcess.startDetached("open", ["-R", path])

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
