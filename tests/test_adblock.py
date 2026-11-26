from collections.abc import Generator
from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings, QUrl

from monobrowser import adblock, session
from monobrowser.utils import internal_url_action

FILTER_SAMPLE = """\
! comment
[Adblock Plus 2.0]
||ads.example.com^
||TRACKER.example.net^
||sub.ads.example.com^
@@||ads.example.com^
||third.example.org^$third-party
||first.example.org^$~third-party
||scoped.example.net^$domain=host.example.com
||excluded.example.net^$domain=~host.example.com
||script.example.com^$script
host.example.com##.ad
"""


@pytest.fixture()
def filters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[Path, None, None]:
    path = tmp_path / "filters.txt"
    path.write_text(FILTER_SAMPLE, encoding="utf-8")
    monkeypatch.setattr(adblock, "ADBLOCK_FILTER_PATHS", (path,))
    adblock.filter_rules.cache_clear()
    adblock.blocked_domains.cache_clear()
    yield path
    adblock.filter_rules.cache_clear()
    adblock.blocked_domains.cache_clear()


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    ini = tmp_path / "session.ini"
    settings = QSettings(str(ini), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_SETTINGS", settings)
    monkeypatch.setattr(session, "_adblock_enabled_cache", None)
    monkeypatch.setattr(session, "_antitrack_enabled_cache", None)
    return settings


def test_filter_rules_parse_domains_and_exceptions(filters: Path) -> None:
    domains = adblock.blocked_domains()
    assert "ads.example.com" in domains
    assert "tracker.example.net" in domains
    assert "sub.ads.example.com" in domains
    assert "third.example.org" in domains
    assert "script.example.com" not in domains
    assert "host.example.com" not in domains
    assert "ads.example.com" in adblock.filter_rules()[0]
    assert adblock.rule_count() > 0


def test_is_blocked_suffix_and_exception(filters: Path) -> None:
    assert adblock.is_blocked("https://tracker.example.net/x") is True
    assert adblock.is_blocked("https://a.b.tracker.example.net/") is True
    assert adblock.is_blocked("https://ads.example.com/banner.js") is False
    assert adblock.is_blocked("https://sub.ads.example.com/x") is False
    assert adblock.is_blocked("https://example.com/") is False
    assert adblock.is_blocked("") is False


def test_is_blocked_case_and_trailing_dot(filters: Path) -> None:
    assert adblock.is_blocked("https://TRACKER.example.net./x") is True


def test_third_party_option(filters: Path) -> None:
    target = "https://third.example.org/x"
    assert adblock.is_blocked(target, "https://other.example/") is True
    assert adblock.is_blocked(target, "https://sub.third.example.org/") is False
    first = "https://first.example.org/x"
    assert adblock.is_blocked(first, "https://other.example/") is False


def test_domain_option(filters: Path) -> None:
    scoped = "https://scoped.example.net/x"
    assert adblock.is_blocked(scoped, "https://host.example.com/") is True
    assert adblock.is_blocked(scoped, "https://other.example/") is False
    excluded = "https://excluded.example.net/x"
    assert adblock.is_blocked(excluded, "https://other.example/") is True
    assert adblock.is_blocked(excluded, "https://host.example.com/") is False


def test_bundled_lists_are_parsed() -> None:
    adblock.filter_rules.cache_clear()
    adblock.blocked_domains.cache_clear()
    assert len(adblock.blocked_domains()) > 1000
    adblock.filter_rules.cache_clear()
    adblock.blocked_domains.cache_clear()


def test_adblock_enabled_default_true(store: QSettings) -> None:
    assert session.adblock_enabled() is True


def test_adblock_enabled_roundtrip(store: QSettings) -> None:
    session.set_adblock_enabled(False)
    assert session.adblock_enabled() is False
    session.set_adblock_enabled(True)
    assert session.adblock_enabled() is True


def test_interceptor_blocks_and_honors_toggle(store: QSettings, filters: Path) -> None:  # type: ignore[no-untyped-def]
    class FakeInfo:
        def __init__(self, url: str, first_party: str = "") -> None:
            self._url = url
            self._first_party = first_party
            self.blocked = False
            self.headers: dict[bytes, bytes] = {}

        def requestUrl(self) -> QUrl:
            return QUrl(self._url)

        def firstPartyUrl(self) -> QUrl:
            return QUrl(self._first_party)

        def block(self, value: bool) -> None:
            self.blocked = value

        def setHttpHeader(self, name: bytes, value: bytes) -> None:
            self.headers[name] = value

    interceptor = adblock.AdblockInterceptor()
    info = FakeInfo("https://tracker.example.net/banner.js", "https://other.example/")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is True

    info = FakeInfo("https://example.com/", "https://example.com/")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is False

    session.set_adblock_enabled(False)
    info = FakeInfo("https://tracker.example.net/banner.js", "https://other.example/")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is False
    assert info.headers == {b"DNT": b"1", b"Sec-GPC": b"1"}


def test_internal_url_action_set_adblock() -> None:
    assert internal_url_action("https://monobrowser.internal/set-adblock?toggle") == (
        "set-adblock",
        "toggle",
    )
    assert internal_url_action("https://monobrowser.internal/set-adblock?") == (
        "",
        "",
    )
    assert internal_url_action("https://monobrowser.internal/set-adblock?on") == (
        "",
        "",
    )


def test_settings_html_adblock_toggle_row() -> None:
    from monobrowser import about_pages

    html = about_pages.settings_html("google", True, "system", True)
    marker = 'href="https://monobrowser.internal/set-adblock?toggle"'
    i = html.index(marker)
    assert 'class="switch on"' in html[max(0, i - 200) : i + 120]
    assert 'aria-checked="true"' in html[max(0, i - 120) : i + 120]
    assert "EasyList + EasyPrivacy" in html
    assert "{{" not in html
    assert any("blocked so far" in ln for ln in html.splitlines())

    html = about_pages.settings_html("google", True, "system", False)
    i = html.index(marker)
    snippet = html[max(0, i - 200) : i + 120]
    assert 'class="switch on"' not in snippet
    assert 'class="switch"' in snippet
    assert 'aria-checked="false"' in snippet


def test_adblock_cosmetic_default_false_and_roundtrip(store: QSettings) -> None:
    assert session.adblock_cosmetic() is False
    session.set_adblock_cosmetic(True)
    assert session.adblock_cosmetic() is True
    session.set_adblock_cosmetic(False)
    assert session.adblock_cosmetic() is False


def test_internal_url_action_set_adblock_cosmetic() -> None:
    assert internal_url_action(
        "https://monobrowser.internal/set-adblock-cosmetic?toggle"
    ) == ("set-adblock-cosmetic", "toggle")
    assert internal_url_action(
        "https://monobrowser.internal/set-adblock-cosmetic?"
    ) == (
        "",
        "",
    )


def test_settings_html_cosmetic_toggle_row() -> None:
    from monobrowser import about_pages

    marker = 'href="https://monobrowser.internal/set-adblock-cosmetic?toggle"'

    html = about_pages.settings_html("google", True, "system", True, True)
    assert marker in html
    assert 'class="switch on" id="cosmetic-switch"' in html
    assert 'aria-checked="true"' in html
    assert "{{" not in html

    html = about_pages.settings_html("google", True, "system", True, False)
    assert marker in html
    assert 'class="switch on" id="cosmetic-switch"' not in html
    assert 'class="switch" id="cosmetic-switch"' in html
    assert 'aria-checked="false"' in html

    html = about_pages.settings_html("google", True, "system", False, True)
    assert marker not in html
    assert 'id="cosmetic-switch"' not in html
