import json
from urllib.parse import quote

DDG_ENDPOINT = "https://duckduckgo.com/ac/?q={}&type=list"
TIMEOUT_MS = 2000
MAX_SUGGESTIONS = 8
MAX_SUGGESTION_LENGTH = 256


def suggestion_url(engine: str, text: str) -> str | None:
    if engine != "duckduckgo":
        return None
    return DDG_ENDPOINT.format(quote(text.strip(), safe=""))


def parse_suggestions(payload: str, limit: int = MAX_SUGGESTIONS) -> list[str]:
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return []
    if not isinstance(data, list) or len(data) < 2:
        return []
    values = data[1]
    if not isinstance(values, list):
        return []
    results: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        text = value.strip()[:MAX_SUGGESTION_LENGTH]
        lowered = text.lower()
        if not text or lowered in seen:
            continue
        seen.add(lowered)
        results.append(text)
        if len(results) >= limit:
            break
    return results
