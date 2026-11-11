from monobrowser import utils
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


def test_internal_action_and_param() -> None:
    bridge = Bridge()
    assert (
        bridge.internalAction("https://monobrowser.internal/set-search?google")
        == "set-search"
    )
    assert (
        bridge.internalParam("https://monobrowser.internal/set-search?google")
        == "google"
    )
    assert (
        bridge.internalAction("https://monobrowser.internal/search?q=hello%20world")
        == "search"
    )
    assert (
        bridge.internalParam("https://monobrowser.internal/search?q=hello%20world")
        == "hello world"
    )
    assert bridge.internalAction("https://example.com/") == ""


def test_icon_url_replaces_current_color() -> None:
    bridge = Bridge()
    url = bridge.iconUrl("lock/lock.svg", "#123456")
    assert url.startswith("data:image/svg+xml;base64,")


def test_html_helpers() -> None:
    bridge = Bridge()
    assert "monobrowser.internal/search" in bridge.newtabHtml()
    setattr(bridge, "searchEngine", "google")
    assert 'class="option selected"' in bridge.settingsHtml()
    assert utils.get_version() in bridge.versionHtml()
