import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from browser import SimpleBrowser
from utils import _is_bundled, get_version, ICON_PATH


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MonoBrowser")
    app.setApplicationVersion(get_version())
    if not _is_bundled():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
