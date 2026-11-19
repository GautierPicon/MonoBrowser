import json
import math
import time
from typing import Any

from PyQt6.QtCore import QSettings

ORG = "MonoBrowser"
APP = "MonoBrowser"
HISTORY_KEY = "history"
MAX_HISTORY = 100
MAX_URL_LENGTH = 4096
MAX_TITLE_LENGTH = 512
MIN_TS = 0

_SETTINGS = QSettings(ORG, APP)


def _is_recordable(url: str) -> bool:
    if not url or len(url) > MAX_URL_LENGTH:
        return False
    lowered = url.lower()
    return not (
        lowered.startswith("about:")
        or lowered.startswith("https://monobrowser.internal")
    )


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
    ts = item.get("ts")
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        ts = 0
    if not math.isfinite(float(ts)):
        ts = 0
    ts = int(max(MIN_TS, float(ts)))
    return {"url": url, "title": title or url, "ts": ts}


def _load() -> list[dict[str, Any]]:
    try:
        raw: Any = _SETTINGS.value(HISTORY_KEY, None)
        if not isinstance(raw, str) or not raw.strip():
            return []
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        items: list[dict[str, Any]] = []
        for entry in data[:MAX_HISTORY]:
            clean = _valid_entry(entry)
            if clean is not None:
                items.append(clean)
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


def record(url: Any, title: Any = "") -> bool:
    if not isinstance(url, str):
        return False
    clean = url.strip()
    if not _is_recordable(clean):
        return False
    clean_title = title.strip()[:MAX_TITLE_LENGTH] if isinstance(title, str) else ""
    items = _load()
    now = int(time.time())
    if items and items[0]["url"] == clean:
        if clean_title:
            items[0]["title"] = clean_title
        items[0]["ts"] = now
        _save(items)
        return True
    items.insert(0, {"url": clean, "title": clean_title or clean, "ts": now})
    _save(items)
    return True


def clear() -> None:
    _SETTINGS.remove(HISTORY_KEY)
    _SETTINGS.sync()
