import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from monobrowser import history
from monobrowser.utils import internal_url_action


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    ini = tmp_path / "history.ini"
    settings = QSettings(str(ini), QSettings.Format.IniFormat)
    monkeypatch.setattr(history, "_SETTINGS", settings)
    return settings


def test_record_and_entries_roundtrip(store: QSettings) -> None:
    assert history.record("https://example.com/", "Example") is True
    items = history.entries()
    assert len(items) == 1
    assert items[0]["url"] == "https://example.com/"
    assert items[0]["title"] == "Example"
    assert items[0]["ts"] > 0


def test_entries_newest_first(store: QSettings) -> None:
    history.record("https://a.example/", "A")
    history.record("https://b.example/", "B")
    items = history.entries()
    assert [item["url"] for item in items] == [
        "https://b.example/",
        "https://a.example/",
    ]


def test_record_skips_about_and_internal_urls(store: QSettings) -> None:
    assert history.record("about:newtab", "New Tab") is False
    assert history.record("https://monobrowser.internal/search?q=x") is False
    assert history.record("", "Empty") is False
    assert history.record("   ", "  ") is False
    assert history.entries() == []


def test_record_dedupes_consecutive_same_url(store: QSettings) -> None:
    history.record("https://example.com/", "Old title")
    history.record("https://example.com/", "New title")
    items = history.entries()
    assert len(items) == 1
    assert items[0]["title"] == "New title"


def test_record_same_url_with_empty_title_keeps_title(store: QSettings) -> None:
    history.record("https://example.com/", "Example")
    history.record("https://example.com/", "")
    items = history.entries()
    assert len(items) == 1
    assert items[0]["title"] == "Example"


def test_record_same_url_non_consecutive_inserts_new_entry(store: QSettings) -> None:
    history.record("https://a.example/", "A")
    history.record("https://b.example/", "B")
    history.record("https://a.example/", "A2")
    items = history.entries()
    assert [item["url"] for item in items] == [
        "https://a.example/",
        "https://b.example/",
        "https://a.example/",
    ]


def test_record_defaults_title_to_url(store: QSettings) -> None:
    history.record("https://example.com/")
    assert history.entries()[0]["title"] == "https://example.com/"


def test_record_caps_at_max_history(store: QSettings) -> None:
    for i in range(history.MAX_HISTORY + 20):
        history.record(f"https://example.com/{i}", f"Page {i}")
    items = history.entries()
    assert len(items) == history.MAX_HISTORY
    assert items[0]["url"] == f"https://example.com/{history.MAX_HISTORY + 19}"
    assert items[-1]["url"] == f"https://example.com/{20}"


def test_clear_removes_all_entries(store: QSettings) -> None:
    history.record("https://example.com/", "Example")
    history.clear()
    assert history.entries() == []


def test_load_corrupted_json_returns_empty(store: QSettings) -> None:
    store.setValue(history.HISTORY_KEY, "{not json")
    assert history.entries() == []


def test_load_wrong_types_drops_invalid_entries(store: QSettings) -> None:
    store.setValue(history.HISTORY_KEY, json.dumps({"not": "a list"}))
    assert history.entries() == []
    store.setValue(
        history.HISTORY_KEY,
        json.dumps(
            [
                {"url": "https://ok.example/", "title": "OK", "ts": 100},
                {"url": 42, "title": "Nope", "ts": 100},
                "garbage",
                {"url": "about:blank", "title": "about", "ts": 100},
            ]
        ),
    )
    items = history.entries()
    assert [item["url"] for item in items] == ["https://ok.example/"]


def test_internal_url_action_clear_history() -> None:
    assert internal_url_action(
        "https://monobrowser.internal/clear-history?confirm"
    ) == ("clear-history", "")
    assert internal_url_action("https://monobrowser.internal/clear-history?") == (
        "clear-history",
        "",
    )
