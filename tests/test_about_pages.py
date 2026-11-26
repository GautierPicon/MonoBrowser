from monobrowser import about_pages, utils


def test_version_html_embeds_version_and_icon() -> None:
    html = about_pages.version_html()
    assert utils.get_version() in html
    assert "data:image/png;base64," in html
    assert "{{" not in html


def test_newtab_html_has_search_form() -> None:
    html = about_pages.newtab_html()
    assert 'action="https://monobrowser.internal/search"' in html
    assert 'name="q"' in html


def test_settings_html_marks_selected_engine() -> None:
    google = about_pages.settings_html("google")
    duckduckgo = about_pages.settings_html("duckduckgo")
    for html, engine in ((google, "google"), (duckduckgo, "duckduckgo")):
        marker = f'href="https://monobrowser.internal/set-search?{engine}"'
        i = html.index(marker)
        snippet = html[max(0, i - 200) : i + 120]
        assert 'class="segment selected"' in snippet
        assert 'aria-checked="true"' in snippet


def test_settings_html_antitrack_toggle_row() -> None:
    marker = 'href="https://monobrowser.internal/set-antitrack?toggle"'
    html = about_pages.settings_html("google", True, "system", True, False, True)
    i = html.index(marker)
    snippet = html[max(0, i - 250) : i + 120]
    assert 'class="switch on" id="antitrack-switch"' in snippet
    assert 'aria-checked="true"' in snippet
    assert "does not block trackers" in html
    assert "{{" not in html

    html = about_pages.settings_html("google", True, "system", True, False, False)
    i = html.index(marker)
    snippet = html[max(0, i - 250) : i + 120]
    assert 'class="switch" id="antitrack-switch"' in snippet
    assert 'aria-checked="false"' in snippet


def test_selected_segment_icon_is_inverted() -> None:
    html = about_pages.settings_html("google")
    assert ".segment.selected .icon { filter: brightness(0) invert(1); }" in html


def test_settings_uses_uniform_controls() -> None:
    html = about_pages.settings_html("google")
    assert 'class="option' not in html
    assert html.count('<a class="switch') == 6
    assert html.count('role="radiogroup"') == 2
    assert 'id="restore-switch"' in html
    assert 'id="cosmetic-rules-switch"' in html
    assert 'class="setting-row"' in html


def test_settings_html_suggestions_toggle_row() -> None:
    marker = 'href="https://monobrowser.internal/set-suggestions?toggle"'
    html = about_pages.settings_html("google", True, "system", True, False, True, True)
    i = html.index(marker)
    snippet = html[max(0, i - 250) : i + 120]
    assert 'class="switch on" id="suggestions-switch"' in snippet
    assert 'aria-checked="true"' in snippet
    assert "Sends what you type to DuckDuckGo" in html
    assert "No suggestion requests are sent with Google selected" in html
    assert "{{" not in html

    html = about_pages.settings_html("google", True, "system", True, False, True, False)
    i = html.index(marker)
    snippet = html[max(0, i - 250) : i + 120]
    assert 'class="switch" id="suggestions-switch"' in snippet
    assert 'aria-checked="false"' in snippet


def test_error_html_escapes_url_and_reason() -> None:
    url = 'https://example.com/<script>alert("x")</script>'
    reason = 'Name not resolved & "host" <unknown>'
    html = about_pages.error_html(url, reason)
    assert "{{" not in html
    assert url not in html
    assert "&lt;script&gt;" in html
    assert "&lt;unknown&gt;" in html
    assert reason not in html
    assert 'class="retry"' in html
    assert utils.INTERNAL_RETRY_BASE in html


def test_error_html_retry_link_roundtrips() -> None:
    target = "https://example.com/?a=b&c=d"
    html = about_pages.error_html(target, "")
    marker = f'href="{utils.INTERNAL_RETRY_BASE}'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    retry_url = "https://monobrowser.internal/retry?url=" + html[start:end]
    assert utils.internal_url_action(retry_url) == ("retry", target)


def test_about_pages_use_mono_favicon() -> None:
    for html in (
        about_pages.version_html(),
        about_pages.newtab_html(),
        about_pages.settings_html("google"),
    ):
        assert '<link rel="icon" href="data:image/svg+xml;base64,' in html
        assert "{{" not in html


def test_error_page_uses_globe_favicon() -> None:
    html = about_pages.error_html("https://example.com/", "boom")
    assert '<link rel="icon" href="data:image/svg+xml;base64,' in html
    assert "{{" not in html


def test_settings_html_marks_selected_theme() -> None:
    for mode in ("system", "light", "dark"):
        html = about_pages.settings_html("google", True, mode)
        marker = f'href="https://monobrowser.internal/set-theme?{mode}"'
        i = html.index(marker)
        snippet = html[max(0, i - 220) : i + 120]
        assert 'class="segment segment-theme selected"' in snippet
        assert 'aria-checked="true"' in snippet
        for other in ("system", "light", "dark"):
            if other != mode:
                j = html.index(f"set-theme?{other}")
                assert 'aria-checked="false"' in html[max(0, j - 220) : j + 120]


def test_theme_dark_renders_dark_palette() -> None:
    html = about_pages.newtab_html("dark")
    assert '<html lang="en" class="theme-dark">' in html
    assert "color-scheme: dark" in html
    assert ".theme-dark body" in html
    assert "@media" not in html


def test_theme_light_renders_light_palette() -> None:
    html = about_pages.newtab_html("light")
    assert '<html lang="en">' in html
    assert "color-scheme: light" in html
    assert 'class="theme-dark"' not in html


def test_theme_system_resolves_without_app_instance() -> None:
    html = about_pages.newtab_html("system")
    assert "color-scheme:" in html
    assert "{{" not in html


def test_all_pages_embed_favicon_and_theme_attr() -> None:
    for html in (
        about_pages.version_html("dark"),
        about_pages.newtab_html("dark"),
        about_pages.settings_html("google", True, "dark"),
        about_pages.error_html("https://x/", "r", "dark"),
    ):
        assert '<html lang="en" class="theme-dark">' in html
        assert "{{" not in html
