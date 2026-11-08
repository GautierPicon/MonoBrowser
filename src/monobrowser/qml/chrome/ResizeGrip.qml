import QtQuick

Item {
    id: root

    property int edge: 0

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: root.Window.startSystemResize(root.edge)
    }
}