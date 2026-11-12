import QtQuick
import ".."

Rectangle {
    id: root

    property string glyph: ""
    property string iconName: ""
    property var bridge: null
    property string tip: ""

    readonly property color iconColor: !root.enabled ? Theme.iconDisabled
         : (hover.hovered ? Theme.textActive : Theme.iconNormal)

    signal clicked()

    implicitWidth: 30
    implicitHeight: 30
    radius: 6
    color: hover.hovered && enabled ? Theme.newtabHover : "transparent"

    IconImage {
        anchors.centerIn: parent
        visible: root.iconName !== ""
        bridge: root.bridge
        iconName: root.iconName
        color: root.iconColor
        size: 16
    }

    Text {
        anchors.centerIn: parent
        visible: root.iconName === ""
        text: root.glyph
        font.pixelSize: 15
        color: root.iconColor
    }

    HoverHandler {
        id: hover
        enabled: root.enabled
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        enabled: root.enabled
        onTapped: root.clicked()
    }
}
