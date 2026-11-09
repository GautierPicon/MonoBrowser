from AppKit import NSApplication, NSWindowCloseButton
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QWindow

TARGET_CENTER = 20.0

_ns_window = None


def _find_window():
    global _ns_window
    for candidate in NSApplication.sharedApplication().windows():
        if not candidate.isVisible():
            continue
        if not candidate.className().startswith("QN"):
            continue
        if candidate.standardWindowButton_(NSWindowCloseButton) is None:
            continue
        _ns_window = candidate
        return _ns_window
    return None


def _center_from_top(ns_window, close):
    host = close.superview()
    rect = host.convertRect_toView_(close.frame(), None)
    content_height = ns_window.contentView().frame().size.height
    return content_height - rect.origin.y - rect.size.height / 2


def align(qt_window):
    if qt_window.visibility() == QWindow.Visibility.FullScreen:
        return
    ns_window = _ns_window if _ns_window is not None else _find_window()
    if ns_window is None:
        return
    close = ns_window.standardWindowButton_(NSWindowCloseButton)
    if close is None:
        return
    host = close.superview()
    current = _center_from_top(ns_window, close)
    shift = TARGET_CENTER - current
    if abs(shift) < 0.25:
        return
    frame = host.frame()
    host.setFrameOrigin_((frame.origin.x, frame.origin.y - shift))


def attach(qt_window):
    align(qt_window)
    qt_window.widthChanged.connect(lambda: align(qt_window))
    qt_window.heightChanged.connect(lambda: align(qt_window))
    qt_window.visibleChanged.connect(lambda: align(qt_window))
    qt_window.visibilityChanged.connect(lambda: align(qt_window))
    QTimer.singleShot(400, lambda: align(qt_window))
