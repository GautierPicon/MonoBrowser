import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from monobrowser.browser import SimpleBrowser
from monobrowser.utils import ICON_PATH, _is_bundled, get_version


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
