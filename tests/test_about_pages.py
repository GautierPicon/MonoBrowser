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
    assert 'class="option selected"' in google
    assert 'class="option selected"' in duckduckgo
    assert google.index('class="option selected"') != duckduckgo.index(
        'class="option selected"'
    )


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
