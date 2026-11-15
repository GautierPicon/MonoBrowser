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
    monkeypatch.setattr(session, "_settings", lambda: settings)
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
