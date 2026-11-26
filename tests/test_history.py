import json
import time
from pathlib import Path
from typing import Any

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


def test_entries_carry_unique_ids(store: QSettings) -> None:
    history.record("https://a.example/", "A")
    history.record("https://b.example/", "B")
    items = history.entries()
    ids = [item["id"] for item in items]
    assert all(ids)
    assert len(set(ids)) == len(ids)


def test_remove_deletes_only_the_targeted_entry(store: QSettings) -> None:
    history.record("https://a.example/", "A")
    history.record("https://b.example/", "B")
    history.record("https://a.example/", "A again")
    items = history.entries()
    target = items[1]["id"]
    assert history.remove(target) is True
    items = history.entries()
    assert [item["url"] for item in items] == [
        "https://a.example/",
        "https://a.example/",
    ]
    assert history.remove(target) is False
    assert history.remove("") is False
    assert history.remove(123) is False


def test_record_dedupes_consecutive_same_url(store: QSettings) -> None:
    history.record("https://example.com/", "Old title")
    history.record("https://example.com/", "New title")
    items = history.entries()
    assert len(items) == 1
    assert items[0]["title"] == "New title"


def test_record_stores_and_backfills_icon(store: QSettings) -> None:
    history.record("https://example.com/", "Example")
    assert history.entries()[0]["icon"] == ""
    history.record("https://example.com/", "Example", "https://example.com/favicon.ico")
    assert history.entries()[0]["icon"] == "https://example.com/favicon.ico"


def test_record_keeps_existing_icon_when_none_provided(store: QSettings) -> None:
    history.record("https://example.com/", "Example", "https://example.com/favicon.ico")
    history.record("https://example.com/", "Example")
    assert history.entries()[0]["icon"] == "https://example.com/favicon.ico"


def test_record_rejects_non_http_icon(store: QSettings) -> None:
    history.record("https://example.com/", "Example", "javascript:alert(1)")
    assert history.entries()[0]["icon"] == ""
    history.record(
        "https://example.com/",
        "Example",
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
    )
    assert history.entries()[0]["icon"].startswith("data:image/png;")


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


def _item(url: str, title: str, ts: float = 0, icon: str = "") -> dict[str, Any]:
    return {"url": url, "title": title, "ts": ts, "icon": icon, "id": "x"}


def test_rank_matches_empty_query_and_clamped_limit() -> None:
    items = [_item("https://github.com/foo", "GitHub")]
    assert history.rank_matches(items, "  ") == []
    assert len(history.rank_matches(items, "git", 0)) == 1
    assert len(history.rank_matches(items, "git", 999)) == 1


def test_rank_matches_prefix_beats_substring() -> None:
    items = [
        _item("https://example.com/pages/git.html", "Version control", 100),
        _item("https://github.com/foo", "GitHub", 0),
    ]
    matches = history.rank_matches(items, "git")
    assert [match["url"] for match in matches] == [
        "https://github.com/foo",
        "https://example.com/pages/git.html",
    ]


def test_rank_matches_recency_breaks_ties() -> None:
    now = time.time()
    items = [
        _item("https://old.example/", "Old", now - 10 * 86400),
        _item("https://new.example/", "New", now),
    ]
    matches = history.rank_matches(items, "example")
    assert matches[0]["url"] == "https://new.example/"


def test_rank_matches_dedupes_url_and_ignores_internal() -> None:
    items = [
        _item("https://github.com/foo", "Old", 0),
        _item("https://monobrowser.internal/search?q=git", "Internal", time.time()),
        _item("https://github.com/foo", "New", time.time()),
    ]
    matches = history.rank_matches(items, "git")
    assert [match["url"] for match in matches] == ["https://github.com/foo"]
    assert matches[0]["title"] == "New"


def test_rank_matches_result_shape() -> None:
    item = _item("https://github.com/foo", "GitHub", time.time(), "https://x/i.ico")
    match = history.rank_matches([item], "git")[0]
    assert match == {
        "url": "https://github.com/foo",
        "title": "GitHub",
        "icon": "https://x/i.ico",
        "source": "history",
        "matched": "url",
    }


def test_rank_matches_marks_title_only_matches() -> None:
    item = _item("https://example.com/page", "Git notes", time.time())
    match = history.rank_matches([item], "git")[0]
    assert match["matched"] == "title"


def test_suggest_reads_stored_history(store: QSettings) -> None:
    history.record("https://github.com/foo", "GitHub")
    history.record("https://example.com/", "Unrelated")
    matches = history.suggest("git")
    assert [match["url"] for match in matches] == ["https://github.com/foo"]


def test_internal_url_action_clear_history() -> None:
    assert internal_url_action(
        "https://monobrowser.internal/clear-history?confirm"
    ) == ("clear-history", "")
    assert internal_url_action("https://monobrowser.internal/clear-history?") == (
        "clear-history",
        "",
    )


def test_internal_url_action_remove_history() -> None:
    assert internal_url_action(
        "https://monobrowser.internal/remove-history?id=abc123"
    ) == ("remove-history", "abc123")
    assert internal_url_action("https://monobrowser.internal/remove-history?") == (
        "",
        "",
    )
    assert internal_url_action("https://monobrowser.internal/remove-history?id=") == (
        "",
        "",
    )
