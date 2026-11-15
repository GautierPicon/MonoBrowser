import json
import math
from typing import Any

from PyQt6.QtCore import QSettings

ORG = "MonoBrowser"
APP = "MonoBrowser"
STATE_KEY = "session"
RESTORE_KEY = "restore_session"
THEME_KEY = "theme_mode"
ADBLOCK_KEY = "adblock_enabled"
ADBLOCK_COSMETIC_KEY = "adblock_cosmetic"
THEME_MODES = ("system", "light", "dark")
MAX_URLS = 50
MAX_URL_LENGTH = 4096
MIN_WIDTH = 480
MIN_HEIGHT = 320


def _settings() -> QSettings:
    return QSettings(ORG, APP)


def restore_enabled() -> bool:
    return _bool_flag(_settings().value(RESTORE_KEY, True), True)


def set_restore_enabled(enabled: bool) -> None:
    _settings().setValue(RESTORE_KEY, bool(enabled))


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return float(value)


def _validate(state: Any) -> dict[str, Any] | None:
    if not isinstance(state, dict):
        return None
    urls = state.get("urls")
    if not isinstance(urls, list):
        return None
    clean_urls: list[str] = []
    for entry in urls[:MAX_URLS]:
        if not isinstance(entry, str):
            return None
        entry = entry.strip()
        if not entry or len(entry) > MAX_URL_LENGTH:
            return None
        clean_urls.append(entry)
    if not clean_urls:
        return None
    index = state.get("current_index", 0)
    if isinstance(index, bool) or not isinstance(index, int):
        index = 0
    index = max(0, min(index, len(clean_urls) - 1))
    geometry = None
    geo = state.get("geometry")
    if isinstance(geo, dict):
        x = _finite_number(geo.get("x"))
        y = _finite_number(geo.get("y"))
        width = _finite_number(geo.get("width"))
        height = _finite_number(geo.get("height"))
        if (
            x is not None
            and y is not None
            and width is not None
            and height is not None
            and width >= MIN_WIDTH
            and height >= MIN_HEIGHT
        ):
            geometry = {
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
                "maximized": bool(geo.get("maximized", False)),
            }
    return {"urls": clean_urls, "current_index": index, "geometry": geometry}


def _bool_flag(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(value, (int, float)):
        return value != 0
    return default


def adblock_enabled() -> bool:
    return _bool_flag(_settings().value(ADBLOCK_KEY, True), True)


def set_adblock_enabled(enabled: bool) -> None:
    _settings().setValue(ADBLOCK_KEY, bool(enabled))


def adblock_cosmetic() -> bool:
    return _bool_flag(_settings().value(ADBLOCK_COSMETIC_KEY, False), False)


def set_adblock_cosmetic(enabled: bool) -> None:
    _settings().setValue(ADBLOCK_COSMETIC_KEY, bool(enabled))


def theme_mode() -> str:
    value: Any = _settings().value(THEME_KEY, "system")
    mode = value.strip().lower() if isinstance(value, str) else "system"
    return mode if mode in THEME_MODES else "system"


def set_theme_mode(mode: str) -> None:
    mode = mode.strip().lower()
    if mode in THEME_MODES:
        _settings().setValue(THEME_KEY, mode)


def load_state() -> dict[str, Any] | None:
    try:
        raw: Any = _settings().value(STATE_KEY, None)
        if not isinstance(raw, str) or not raw.strip():
            return None
        return _validate(json.loads(raw))
    except Exception:
        return None


def save_state(
    urls: Any,
    current_index: Any,
    x: Any,
    y: Any,
    width: Any,
    height: Any,
    maximized: Any,
) -> None:
    try:
        clean_urls: list[str] = []
        if isinstance(urls, (list, tuple)):
            for entry in list(urls)[:MAX_URLS]:
                if isinstance(entry, str):
                    entry = entry.strip()
                    if entry and len(entry) <= MAX_URL_LENGTH:
                        clean_urls.append(entry)
        if not clean_urls:
            return
        index = current_index
        if isinstance(index, bool) or not isinstance(index, int):
            index = 0
        index = max(0, min(index, len(clean_urls) - 1))
        geo_x = _finite_number(x) or 0.0
        geo_y = _finite_number(y) or 0.0
        geo_width = _finite_number(width) or 1200.0
        geo_height = _finite_number(height) or 800.0
        state = {
            "urls": clean_urls,
            "current_index": index,
            "geometry": {
                "x": int(geo_x),
                "y": int(geo_y),
                "width": int(geo_width),
                "height": int(geo_height),
                "maximized": bool(maximized),
            },
        }
        _settings().setValue(STATE_KEY, json.dumps(state))
    except Exception:
        return
