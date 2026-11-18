import QtQuick
import "../chrome"

Rectangle {
    id: button

    property var bridge: null
    property string iconName: ""

    signal tapped()

    width: 24
    height: 24
    radius: 12
    color: buttonHover.hovered ? "#4D000000" : "transparent"

    IconImage {
        anchors.centerIn: parent
        bridge: button.bridge
        iconName: button.iconName
        color: "#FFFFFF"
        size: 13
    }

    HoverHandler { id: buttonHover; cursorShape: Qt.PointingHandCursor }
    TapHandler { onTapped: button.tapped() }
}
