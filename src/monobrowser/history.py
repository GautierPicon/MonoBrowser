import json
import math
import re
import time
import uuid
from typing import Any
from urllib.parse import urlsplit

from PyQt6.QtCore import QSettings

ORG = "MonoBrowser"
APP = "MonoBrowser"
HISTORY_KEY = "history"
MAX_HISTORY = 100
MAX_URL_LENGTH = 4096
MAX_TITLE_LENGTH = 512
MAX_ICON_LENGTH = 16384
ICON_SCHEMES = ("https://", "http://", "data:image/")
MIN_TS = 0
MAX_SUGGESTIONS = 8
MAX_SUGGEST_LIMIT = 20

_SETTINGS = QSettings(ORG, APP)


def _is_recordable(url: str) -> bool:
    if not url or len(url) > MAX_URL_LENGTH:
        return False
    lowered = url.lower()
    return not (
        lowered.startswith("about:")
        or lowered.startswith("https://monobrowser.internal")
    )


def _valid_icon(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    icon = value.strip()
    if not icon or len(icon) > MAX_ICON_LENGTH:
        return ""
    for scheme in ICON_SCHEMES:
        if icon.startswith(scheme):
            return icon
    return ""


def _valid_entry(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    url = item.get("url")
    if not isinstance(url, str):
        return None
    url = url.strip()
    if not _is_recordable(url):
        return None
    title = item.get("title")
    title = title.strip()[:MAX_TITLE_LENGTH] if isinstance(title, str) else ""
    icon = _valid_icon(item.get("icon"))
    ts = item.get("ts")
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        ts = 0
    if not math.isfinite(float(ts)):
        ts = 0
    ts = int(max(MIN_TS, float(ts)))
    entry_id = item.get("id")
    entry_id = entry_id.strip() if isinstance(entry_id, str) else ""
    if not entry_id or len(entry_id) > 64:
        entry_id = uuid.uuid4().hex
    return {"url": url, "title": title or url, "ts": ts, "icon": icon, "id": entry_id}


def _load() -> list[dict[str, Any]]:
    try:
        raw: Any = _SETTINGS.value(HISTORY_KEY, None)
        if not isinstance(raw, str) or not raw.strip():
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        items: list[dict[str, Any]] = []
        migrated = False
        for entry in data[:MAX_HISTORY]:
            had_id = isinstance(entry, dict) and isinstance(entry.get("id"), str)
            clean = _valid_entry(entry)
            if clean is not None:
                items.append(clean)
                if not had_id or not entry["id"].strip() or len(entry["id"]) > 64:
                    migrated = True
        if migrated:
            _save(items)
        return items
    except Exception:
        return []


def _save(items: list[dict[str, Any]]) -> None:
    try:
        _SETTINGS.setValue(HISTORY_KEY, json.dumps(items[:MAX_HISTORY]))
        _SETTINGS.sync()
    except Exception:
        return


def entries() -> list[dict[str, Any]]:
    return _load()


def _match_score(query: str, url: str, title: str, host: str) -> int:
    if query in (url, title, host):
        return 4
    if url.startswith(query) or title.startswith(query) or host.startswith(query):
        return 3
    words = re.split(r"[^a-z0-9]+", host + " " + title)
    if any(word.startswith(query) for word in words if word):
        return 2
    if query in url or query in title:
        return 1
    return 0


def rank_matches(
    items: list[dict[str, Any]], text: str, limit: int = MAX_SUGGESTIONS
) -> list[dict[str, Any]]:
    query = text.strip().lower()
    if not query:
        return []
    if isinstance(limit, bool) or not isinstance(limit, int):
        limit = MAX_SUGGESTIONS
    limit = max(1, min(limit, MAX_SUGGEST_LIMIT))

    now = time.time()
    best: dict[str, tuple[tuple[int, float, int], dict[str, Any]]] = {}
    for index, item in enumerate(items):
        url = str(item.get("url", "") or "").strip()
        if not _is_recordable(url):
            continue
        title = str(item.get("title", "") or "") or url
        try:
            host = urlsplit(url).hostname or ""
        except ValueError:
            host = ""
        score = _match_score(query, url.lower(), title.lower(), host.lower())
        if score == 0:
            continue
        ts = item.get("ts")
        if (
            isinstance(ts, bool)
            or not isinstance(ts, (int, float))
            or not math.isfinite(ts)
        ):
            ts = 0
        age_days = max(0.0, (now - float(ts)) / 86400.0)
        key = (score, 1.0 / (1.0 + age_days / 7.0), -index)
        entry = {
            "url": url,
            "title": title,
            "icon": str(item.get("icon", "") or ""),
            "source": "history",
        }
        previous = best.get(url)
        if previous is None or key > previous[0]:
            best[url] = (key, entry)

    ranked = sorted(best.values(), key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in ranked[:limit]]


def suggest(text: str, limit: int = MAX_SUGGESTIONS) -> list[dict[str, Any]]:
    return rank_matches(entries(), text, limit)


def record(url: Any, title: Any = "", icon: Any = "") -> bool:
    if not isinstance(url, str):
        return False
    clean = url.strip()
    if not _is_recordable(clean):
        return False
    clean_title = title.strip()[:MAX_TITLE_LENGTH] if isinstance(title, str) else ""
    clean_icon = _valid_icon(icon)
    items = _load()
    now = int(time.time())
    if items and items[0]["url"] == clean:
        if clean_title:
            items[0]["title"] = clean_title
        if clean_icon and items[0]["icon"] != clean_icon:
            items[0]["icon"] = clean_icon
        items[0]["ts"] = now
        _save(items)
        return True
    items.insert(
        0,
        {
            "url": clean,
            "title": clean_title or clean,
            "ts": now,
            "icon": clean_icon,
            "id": uuid.uuid4().hex,
        },
    )
    _save(items)
    return True


def remove(entry_id: Any) -> bool:
    if not isinstance(entry_id, str):
        return False
    target = entry_id.strip()
    if not target:
        return False
    items = _load()
    kept = [item for item in items if item.get("id") != target]
    if len(kept) == len(items):
        return False
    _save(kept)
    return True


def clear() -> None:
    _SETTINGS.remove(HISTORY_KEY)
    _SETTINGS.sync()
