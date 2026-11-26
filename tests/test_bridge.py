from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from monobrowser import history, session, utils
from monobrowser.bridge import Bridge


def test_resolve_address_uses_search_engine() -> None:
    bridge = Bridge()
    assert bridge.resolveAddress("example.com") == "https://example.com"
    assert (
        bridge.resolveAddress("chat mignon")
        == "https://duckduckgo.com/?q=chat%20mignon"
    )
    setattr(bridge, "searchEngine", "google")
    assert getattr(bridge, "searchEngine") == "google"
    assert bridge.resolveAddress("chat mignon").startswith(
        "https://www.google.com/search?q="
    )


def test_suggest_matches_slot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = QSettings(str(tmp_path / "history.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(history, "_SETTINGS", settings)
    history.record("https://github.com/foo", "GitHub")

    bridge = Bridge()
    matches = bridge.suggestMatches("git", 5)
    assert len(matches) == 1
    assert matches[0]["url"] == "https://github.com/foo"
    assert bridge.suggestMatches("", 5) == []


def test_request_suggestions_is_gated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = QSettings(str(tmp_path / "session.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_SETTINGS", settings)
    monkeypatch.setattr(session, "_antitrack_enabled_cache", None)

    class FakeManager:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def get(self, request: object) -> None:
            self.calls.append(request.url().toString())  # type: ignore[attr-defined]
            return None

    bridge = Bridge()
    manager = FakeManager()
    setattr(bridge, "_suggestions_manager", manager)

    bridge.requestSuggestions("git")
    assert len(manager.calls) == 1
    assert manager.calls[0] == "https://duckduckgo.com/ac/?q=git&type=list"

    setattr(bridge, "suggestionsEnabled", False)
    bridge.requestSuggestions("git")
    assert len(manager.calls) == 1

    setattr(bridge, "suggestionsEnabled", True)
    setattr(bridge, "searchEngine", "google")
    bridge.requestSuggestions("git")
    assert len(manager.calls) == 1

    setattr(bridge, "searchEngine", "duckduckgo")
    bridge.requestSuggestions("github.com")
    assert len(manager.calls) == 1


def test_external_url_slots() -> None:
    bridge = Bridge()
    assert bridge.isExternalUrl("mailto:foo@bar") is True
    assert bridge.isExternalUrl("magnet:?xt=urn:btih:abc") is True
    assert bridge.isExternalUrl("https://example.com/") is False
    assert bridge.isExternalUrl("javascript:alert(1)") is False
    assert bridge.isExternalUrl("file:///tmp/a.html") is False


def test_internal_route() -> None:
    bridge = Bridge()
    assert bridge.internalRoute("https://monobrowser.internal/set-search?google") == [
        "set-search",
        "google",
    ]
    assert bridge.internalRoute(
        "https://monobrowser.internal/search?q=hello%20world"
    ) == ["search", "hello world"]
    assert bridge.internalRoute("https://example.com/") == ["", ""]


def test_icon_url_replaces_current_color() -> None:
    bridge = Bridge()
    url = bridge.iconUrl("svg/lock/lock.svg", "#123456")
    assert url.startswith("data:image/svg+xml;base64,")


def test_antitrack_enabled_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = QSettings(str(tmp_path / "session.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_SETTINGS", settings)
    monkeypatch.setattr(session, "_antitrack_enabled_cache", None)

    bridge = Bridge()
    assert bridge.antitrackEnabled is True
    setattr(bridge, "antitrackEnabled", False)
    assert bridge.antitrackEnabled is False
    html = bridge.settingsHtml()
    marker = 'href="https://monobrowser.internal/set-antitrack?toggle"'
    i = html.index(marker)
    assert 'aria-checked="false"' in html[max(0, i - 250) : i + 120]

    setattr(bridge, "antitrackEnabled", True)
    assert bridge.antitrackEnabled is True


def test_html_helpers() -> None:
    bridge = Bridge()
    assert "monobrowser.internal/search" in bridge.newtabHtml()
    setattr(bridge, "searchEngine", "google")
    assert 'class="option selected"' in bridge.settingsHtml()
    assert utils.get_version() in bridge.versionHtml()
