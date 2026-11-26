import json
from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from monobrowser import session
from monobrowser.utils import internal_url_action


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    ini = tmp_path / "session.ini"
    settings = QSettings(str(ini), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_SETTINGS", settings)
    monkeypatch.setattr(session, "_adblock_enabled_cache", None)
    monkeypatch.setattr(session, "_antitrack_enabled_cache", None)
    return settings


def test_restore_enabled_defaults_to_true(store: QSettings) -> None:
    assert session.restore_enabled() is True


def test_restore_flag_roundtrip(store: QSettings) -> None:
    session.set_restore_enabled(False)
    assert session.restore_enabled() is False
    session.set_restore_enabled(True)
    assert session.restore_enabled() is True


def test_save_and_load_roundtrip(store: QSettings) -> None:
    session.save_state(
        ["https://example.com/", "about:newtab"], 1, 10, 20, 1440, 900, True
    )
    state = session.load_state()
    assert state is not None
    assert state["urls"] == ["https://example.com/", "about:newtab"]
    assert state["current_index"] == 1
    assert state["geometry"] == {
        "x": 10,
        "y": 20,
        "width": 1440,
        "height": 900,
        "maximized": True,
    }


def test_load_state_corrupted_json(store: QSettings) -> None:
    store.setValue(session.STATE_KEY, "{not json")
    assert session.load_state() is None


def test_load_state_wrong_types(store: QSettings) -> None:
    store.setValue(session.STATE_KEY, json.dumps({"urls": "https://example.com"}))
    assert session.load_state() is None
    store.setValue(session.STATE_KEY, json.dumps({"urls": [123]}))
    assert session.load_state() is None
    store.setValue(session.STATE_KEY, json.dumps(["not", "a", "dict"]))
    assert session.load_state() is None


def test_load_state_clamps_current_index(store: QSettings) -> None:
    store.setValue(
        session.STATE_KEY,
        json.dumps(
            {
                "urls": ["https://a.example/", "https://b.example/"],
                "current_index": 99,
            }
        ),
    )
    state = session.load_state()
    assert state is not None
    assert state["current_index"] == 1


def test_load_state_drops_invalid_geometry(store: QSettings) -> None:
    store.setValue(
        session.STATE_KEY,
        json.dumps(
            {
                "urls": ["https://example.com/"],
                "current_index": 0,
                "geometry": {
                    "x": 0,
                    "y": 0,
                    "width": 10,
                    "height": 10,
                    "maximized": True,
                },
            }
        ),
    )
    state = session.load_state()
    assert state is not None
    assert state["geometry"] is None


def test_load_state_missing_returns_none(store: QSettings) -> None:
    assert session.load_state() is None


def test_save_state_skips_invalid_urls(store: QSettings) -> None:
    session.save_state(
        ["", "  ", 42, "https://example.com/"],  # type: ignore[list-item]
        0,
        0,
        0,
        1200,
        800,
        False,
    )
    state = session.load_state()
    assert state is not None
    assert state["urls"] == ["https://example.com/"]


def test_save_state_without_valid_urls_writes_nothing(store: QSettings) -> None:
    session.save_state(["", 42], 0, 0, 0, 1200, 800, False)  # type: ignore[list-item]
    assert session.load_state() is None


def test_internal_url_action_set_restore() -> None:
    assert internal_url_action("https://monobrowser.internal/set-restore?toggle") == (
        "set-restore",
        "toggle",
    )
    assert internal_url_action("https://monobrowser.internal/set-restore?") == ("", "")
    assert internal_url_action("https://monobrowser.internal/set-restore?nope") == (
        "",
        "",
    )


def test_save_session_slot_arity_matches_qml_call() -> None:
    from PyQt6.QtCore import QMetaMethod

    from monobrowser.bridge import Bridge

    slots = [
        Bridge.staticMetaObject.method(i)
        for i in range(Bridge.staticMetaObject.methodCount())
        if Bridge.staticMetaObject.method(i).methodType() == QMetaMethod.MethodType.Slot
        and Bridge.staticMetaObject.method(i).name().data().decode() == "saveSession"
    ]
    assert len(slots) == 1
    assert slots[0].parameterCount() == 7


def test_cosmetic_rules_default_false_and_roundtrip(store: QSettings) -> None:
    assert session.cosmetic_rules_enabled() is False
    session.set_cosmetic_rules_enabled(True)
    assert session.cosmetic_rules_enabled() is True
    session.set_cosmetic_rules_enabled(False)
    assert session.cosmetic_rules_enabled() is False


def test_antitrack_enabled_default_true(store: QSettings) -> None:
    assert session.antitrack_enabled() is True


def test_antitrack_flag_roundtrip(store: QSettings) -> None:
    session.set_antitrack_enabled(False)
    assert session.antitrack_enabled() is False
    session.set_antitrack_enabled(True)
    assert session.antitrack_enabled() is True


def test_suggestions_enabled_default_true(store: QSettings) -> None:
    assert session.suggestions_enabled() is True


def test_suggestions_flag_roundtrip(store: QSettings) -> None:
    session.set_suggestions_enabled(False)
    assert session.suggestions_enabled() is False
    session.set_suggestions_enabled(True)
    assert session.suggestions_enabled() is True


def test_theme_mode_defaults_to_system(store: QSettings) -> None:
    assert session.theme_mode() == "system"


def test_theme_mode_roundtrip(store: QSettings) -> None:
    for mode in ("light", "dark", "system"):
        session.set_theme_mode(mode)
        assert session.theme_mode() == mode


def test_theme_mode_invalid_falls_back_to_system(store: QSettings) -> None:
    store.setValue(session.THEME_KEY, "banana")
    assert session.theme_mode() == "system"
    session.set_theme_mode("banana")
    assert session.theme_mode() == "system"
