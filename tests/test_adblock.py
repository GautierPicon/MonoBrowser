from pathlib import Path

import pytest
from PyQt6.QtCore import QSettings, QUrl

from monobrowser import adblock, session
from monobrowser.utils import internal_url_action

HOSTS_SAMPLE = """\
# a comment
0.0.0.0 ads.example.com
0.0.0.0 TRACKER.example.net
127.0.0.1 localhost
::1 ip6-localhost
0.0.0.0 ads.example.com

malware.example.org # trailing comment
0.0.0.0 notadomain
"""


@pytest.fixture()
def hosts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    path = tmp_path / "hosts.txt"
    path.write_text(HOSTS_SAMPLE, encoding="utf-8")
    monkeypatch.setattr(adblock, "ADBLOCK_HOSTS_PATH", path)
    adblock.blocked_domains.cache_clear()
    yield path
    adblock.blocked_domains.cache_clear()


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> QSettings:
    ini = tmp_path / "session.ini"
    settings = QSettings(str(ini), QSettings.Format.IniFormat)
    monkeypatch.setattr(session, "_settings", lambda: settings)
    return settings


def test_blocked_domains_parse_dedup_normalize(hosts: Path) -> None:
    domains = adblock.blocked_domains()
    assert "ads.example.com" in domains
    assert "tracker.example.net" in domains
    assert "malware.example.org" in domains
    assert "localhost" not in domains
    assert "ip6-localhost" not in domains
    assert "notadomain" not in domains


def test_blocked_domains_suffix_and_subdomain(hosts: Path) -> None:
    assert adblock.is_blocked("ads.example.com")
    assert adblock.is_blocked("sub.ads.example.com")
    assert adblock.is_blocked("a.b.tracker.example.net")
    assert not adblock.is_blocked("example.com")
    assert not adblock.is_blocked("notads.example.com")
    assert not adblock.is_blocked("")


def test_is_blocked_case_and_trailing_dot(hosts: Path) -> None:
    assert adblock.is_blocked("ADS.EXAMPLE.COM")
    assert adblock.is_blocked("ads.example.com.")


def test_adblock_enabled_default_true(store: QSettings) -> None:
    assert session.adblock_enabled() is True


def test_adblock_enabled_roundtrip(store: QSettings) -> None:
    session.set_adblock_enabled(False)
    assert session.adblock_enabled() is False
    session.set_adblock_enabled(True)
    assert session.adblock_enabled() is True


def test_interceptor_blocks_and_honors_toggle(store: QSettings, hosts: Path) -> None:  # type: ignore[no-untyped-def]
    class FakeInfo:
        def __init__(self, url: str) -> None:
            self._url = url
            self.blocked = False

        def requestUrl(self) -> QUrl:
            return QUrl(self._url)

        def block(self, value: bool) -> None:
            self.blocked = value

    interceptor = adblock.AdblockInterceptor()
    info = FakeInfo("https://ads.example.com/banner.js")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is True

    info = FakeInfo("https://example.com/")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is False

    session.set_adblock_enabled(False)
    info = FakeInfo("https://ads.example.com/banner.js")
    interceptor.interceptRequest(info)  # type: ignore[arg-type]
    assert info.blocked is False


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
    line = next(ln for ln in html.splitlines() if marker in ln)
    assert 'class="btn on"' in line
    assert ">Enabled<" in line
    assert "{{" not in html

    html = about_pages.settings_html("google", True, "system", True, False)
    line = next(ln for ln in html.splitlines() if marker in ln)
    assert 'class="btn on"' not in line
    assert ">Disabled<" in line
