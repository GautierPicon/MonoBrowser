from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings

from monobrowser import about_pages, history, utils


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    ini = tmp_path / "history.ini"
    settings = QSettings(str(ini), QSettings.Format.IniFormat)
    monkeypatch.setattr(history, "_SETTINGS", settings)
    return settings


def test_history_html_empty_state(store: QSettings) -> None:
    html = about_pages.history_html("dark")
    assert "0 entries" in html
    assert "No history yet." in html
    assert "{{" not in html
    assert '<html lang="en" class="theme-dark">' in html
    assert utils.INTERNAL_CLEAR_HISTORY_BASE in html


def test_history_html_lists_entries(store: QSettings) -> None:
    history.record("https://example.com/", "Example Site")
    html = about_pages.history_html()
    assert "1 entry" in html
    assert "Example Site" in html
    assert "https://example.com/" in html
    assert "Clear history" in html
    assert "{{" not in html


def test_history_html_escapes_url_and_title(store: QSettings) -> None:
    history.record(
        "https://example.com/?a=<script>alert(1)</script>",
        '<img src=x onerror="alert(2)">',
    )
    html = about_pages.history_html()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert 'onerror="alert(2)">' not in html


def test_history_html_renders_favicon(store: QSettings) -> None:
    history.record(
        "https://example.com/", "Example Site", "https://example.com/favicon.ico"
    )
    html = about_pages.history_html()
    assert 'class="favicon"' in html
    assert 'src="https://example.com/favicon.ico"' in html


def test_history_html_falls_back_to_monogram_without_icon(
    store: QSettings,
) -> None:
    history.record("https://example.com/", "Example Site")
    html = about_pages.history_html()
    assert 'class="favicon"' not in html
    assert 'class="monogram"' in html


def test_history_html_search_data_attribute(store: QSettings) -> None:
    history.record("https://Example.com/Path", "My Title")
    html = about_pages.history_html()
    assert 'data-search="my title https://example.com/path"' in html
