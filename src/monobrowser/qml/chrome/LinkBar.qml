import QtQuick
import ".."

Rectangle {
    id: root

    property string target: ""

    visible: target !== ""
    height: 22
    radius: 6
    color: Theme.menuBg
    border.width: 1
    border.color: Theme.menuBorder

    Text {
        id: label
        anchors.left: parent.left
        anchors.leftMargin: 8
        anchors.right: parent.right
        anchors.rightMargin: 8
        anchors.verticalCenter: parent.verticalCenter
        text: root.target
        color: Theme.menuText
        font.pixelSize: 11
        elide: Text.ElideMiddle
        verticalAlignment: Text.AlignVCenter
    }

    width: Math.min(480, label.implicitWidth + 16)
}
