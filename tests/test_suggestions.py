from monobrowser import suggestions


def test_suggestion_url_is_duckduckgo_only() -> None:
    assert suggestions.suggestion_url("duckduckgo", " git ") == (
        "https://duckduckgo.com/ac/?q=git&type=list"
    )
    assert suggestions.suggestion_url("google", "git") is None
    assert suggestions.suggestion_url("unknown", "git") is None


def test_suggestion_url_queries_special_characters() -> None:
    url = suggestions.suggestion_url("duckduckgo", "git hub & cie")
    assert url is not None
    assert "git%20hub%20%26%20cie" in url


def test_parse_suggestions() -> None:
    payload = '["git", ["github", "gitlab", "github desktop"]]'
    assert suggestions.parse_suggestions(payload) == [
        "github",
        "gitlab",
        "github desktop",
    ]


def test_parse_suggestions_dedupes_and_limits() -> None:
    payload = '["git", ["GitHub", "github", "", 42, "gitlab", "gitee"]]'
    assert suggestions.parse_suggestions(payload, 2) == ["GitHub", "gitlab"]


def test_parse_suggestions_rejects_malformed_payloads() -> None:
    for payload in ("", "not json", "[]", '["git"]', '["git", "no"]', "{}"):
        assert suggestions.parse_suggestions(payload) == []
