import QtQuick
import QtQuick.Controls as C
import ".."

C.MenuItem {
    id: control

    implicitHeight: 26
    padding: 0
    spacing: 0

    contentItem: Item {
        implicitWidth: control.checkable ? 34 + label.implicitWidth : label.implicitWidth + 20
        implicitHeight: 26

        Text {
            id: checkLabel
            width: 10
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            visible: control.checkable
            text: control.checked ? "✓" : ""
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            color: control.highlighted ? Theme.menuHoverText : Theme.menuText
        }

        Text {
            id: label
            anchors.left: control.checkable ? checkLabel.right : parent.left
            anchors.leftMargin: control.checkable ? 4 : 10
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            elide: Text.ElideRight
            font.pixelSize: 13
            color: !control.enabled ? Theme.menuTextDim
                 : (control.highlighted ? Theme.menuHoverText : Theme.menuText)
        }
    }

    background: Rectangle {
        radius: 5
        color: control.enabled && control.highlighted ? Theme.menuHover : "transparent"
    }
}
