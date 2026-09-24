from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton

from monobrowser.utils import _assets_path


def nav_button(icon_name: str, fallback_text: str, tooltip: str) -> QPushButton:
    button = QPushButton()
    icon_path = _assets_path(icon_name)
    if icon_path.exists():
        button.setIcon(QIcon(str(icon_path)))
        button.setIconSize(QSize(18, 18))
    else:
        button.setText(fallback_text)
    button.setToolTip(tooltip)
    button.setFixedWidth(30)
    return button
