from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInfo

from monobrowser import session

TRACKING_HEADERS = ((b"DNT", b"1"), (b"Sec-GPC", b"1"))


def apply_tracking_headers(info: QWebEngineUrlRequestInfo) -> None:
    if not session.antitrack_enabled():
        return
    for name, value in TRACKING_HEADERS:
        info.setHttpHeader(name, value)
