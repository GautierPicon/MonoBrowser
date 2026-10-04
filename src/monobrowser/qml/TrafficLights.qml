import QtQuick
import QtQuick.Controls

Item {
    id: root
    width: 78

    property bool windowActive: true
    property int hovered: -1

    signal activated(int index)

    readonly property var colors: [Theme.trafficClose, Theme.trafficMinimize, Theme.trafficZoom]
    readonly property var glyphs: ["×", "–", "+"]
    readonly property var tips: ["Close", "Minimize", "Zoom"]

    Row {
        id: group
        anchors.centerIn: parent
        spacing: 8

        Repeater {
            model: 3
            Rectangle {
                id: dot
                width: 12
                height: 12
                radius: 6
                color: root.windowActive ? root.colors[index] : Theme.trafficInactive
                border.width: 1
                border.color: Qt.darker(color, 1.35)

                Text {
                    anchors.centerIn: parent
                    text: root.glyphs[index]
                    font.pixelSize: 9
                    color: "#00000099"
                    visible: root.hovered >= 0 && root.windowActive
                }

                MouseArea {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onEntered: root.hovered = index
                    onExited: root.hovered = -1
                    onClicked: root.activated(index)

                    ToolTip.text: root.tips[index]
                    ToolTip.visible: containsMouse
                }
            }
        }
    }
}
