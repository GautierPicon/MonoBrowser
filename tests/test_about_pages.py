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
