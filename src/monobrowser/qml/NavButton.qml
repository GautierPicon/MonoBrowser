import QtQuick

Rectangle {
    id: root

    property string glyph: ""
    property string tip: ""

    signal clicked()

    implicitWidth: 30
    implicitHeight: 30
    radius: 6
    color: hover.hovered && enabled ? Theme.newtabHover : "transparent"

    Text {
        anchors.centerIn: parent
        text: root.glyph
        font.pixelSize: 15
        color: !root.enabled ? Theme.iconDisabled
             : (hover.hovered ? Theme.textActive : Theme.iconNormal)
        opacity: root.enabled ? 1.0 : 0.9
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
