import os
import sys

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

from monobrowser.bridge import Bridge
from monobrowser.utils import ICON_PATH, _is_bundled, get_version, qml_path

QML_DIR = qml_path("").parent


def main():
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("MonoBrowser")
    app.setApplicationVersion(get_version())
    if not _is_bundled():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    engine = QQmlApplicationEngine()
    engine.warnings.connect(
        lambda errors: print("QML warnings:", errors, file=sys.stderr)
    )
    engine.addImportPath(str(QML_DIR))
    bridge = Bridge()
    engine.rootContext().setContextProperty("bridge", bridge)

    main_qml = qml_path("Main.qml")
    if not main_qml.exists():
        print(f"missing QML entrypoint: {main_qml}", file=sys.stderr)
        sys.exit(1)

    engine.load(QUrl.fromLocalFile(str(main_qml)))
    if not engine.rootObjects():
        print(f"failed to load {main_qml}", file=sys.stderr)
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
