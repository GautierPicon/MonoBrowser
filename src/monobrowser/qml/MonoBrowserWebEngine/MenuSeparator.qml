import QtQuick
import QtQuick.Controls as C
import ".."

C.MenuSeparator {
    id: control

    padding: 0
    horizontalPadding: 8
    verticalPadding: 5

    contentItem: Rectangle {
        implicitHeight: 1
        color: Theme.menuBorder
    }
}
