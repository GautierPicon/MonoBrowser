from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from monobrowser import privacy, session


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    settings = QSettings(str(tmp_path / "session.ini"), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_SETTINGS", settings)
    monkeypatch.setattr(session, "_antitrack_enabled_cache", None)
    return settings


class FakeInfo:
    def __init__(self) -> None:
        self.headers: dict[bytes, bytes] = {}

    def setHttpHeader(self, name: bytes, value: bytes) -> None:
        self.headers[name] = value


def test_tracking_headers_sent_by_default(store: QSettings) -> None:
    info = FakeInfo()
    privacy.apply_tracking_headers(info)  # type: ignore[arg-type]
    assert info.headers == {b"DNT": b"1", b"Sec-GPC": b"1"}


def test_tracking_headers_absent_when_disabled(store: QSettings) -> None:
    session.set_antitrack_enabled(False)
    info = FakeInfo()
    privacy.apply_tracking_headers(info)  # type: ignore[arg-type]
    assert info.headers == {}
