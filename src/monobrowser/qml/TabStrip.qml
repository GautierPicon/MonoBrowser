import QtQuick
import QtQuick.Controls

Item {
    id: root

    property var tabModel: null
    property int currentIndex: -1

    signal tabClicked(int index)
    signal tabClosed(int index)
    signal newTabRequested()
    signal backgroundPressed()

    implicitHeight: 40

    Rectangle {
        anchors.fill: parent
        color: "transparent"
    }

    Row {
        id: strip
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: 0

        Repeater {
            model: root.tabModel

            delegate: Item {
                id: tabDelegate
                readonly property bool isCurrent: index === root.currentIndex
                required property int index
                required property string title
                required property string favicon

                width: Math.max(110, Math.min(240, 20 + faviconWidth + 8 + titleWidth + 8 + 22 + 10))
                height: 38

                readonly property int faviconWidth: favicon !== "" ? 16 : 0
                readonly property int titleWidth: Math.min(
                    180, Math.ceil(implicitText.implicitWidth))

                Rectangle {
                    anchors.fill: parent
                    anchors.topMargin: 2
                    radius: 9
                    color: tabDelegate.isCurrent ? Theme.tabActiveBg
                         : (hover.hovered ? Theme.tabHoverBg : "transparent")
                    border.width: tabDelegate.isCurrent ? 1 : 0
                    border.color: Theme.border

                    Behavior on color {
                        ColorAnimation { duration: 90 }
                    }
                }

                Image {
                    id: icon
                    visible: tabDelegate.faviconWidth > 0
                    width: 16
                    height: 16
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    source: tabDelegate.favicon
                    asynchronous: true
                    fillMode: Image.PreserveAspectFit
                }

                Text {
                    id: implicitText
                    visible: false
                    text: tabDelegate.title !== "" ? tabDelegate.title : "New Tab"
                    font.pixelSize: 13
                }

                Text {
                    id: label
                    anchors.left: icon.visible ? icon.right : parent.left
                    anchors.leftMargin: icon.visible ? 8 : 10
                    anchors.right: closeButton.left
                    anchors.rightMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    text: tabDelegate.title !== "" ? tabDelegate.title : "New Tab"
                    elide: Text.ElideRight
                    font.pixelSize: 13
                    color: tabDelegate.isCurrent ? Theme.textActive : Theme.textInactive
                }

                Rectangle {
                    id: closeButton
                    visible: tabDelegate.isCurrent || hover.hovered
                    width: 22
                    height: 22
                    radius: 11
                    anchors.right: parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    color: closeHover.hovered ? Theme.closeHoverBg : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        font.pixelSize: 11
                        color: Theme.closeGlyph
                    }

                    HoverHandler { id: closeHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler {
                        acceptedButtons: Qt.LeftButton
                        onTapped: root.tabClosed(tabDelegate.index)
                    }
                }

                HoverHandler { id: hover }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: root.tabClicked(tabDelegate.index)
                }
            }
        }
    }

    Rectangle {
        id: newTabButton
        width: 28
        height: 28
        radius: 14
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: strip.right
        anchors.leftMargin: 6
        color: newTabHover.hovered ? Theme.newtabHover : "transparent"

        Text {
            anchors.centerIn: parent
            text: "+"
            font.pixelSize: 18
            color: newTabHover.hovered ? Theme.textActive : Theme.textInactive
        }

        HoverHandler { id: newTabHover; cursorShape: Qt.PointingHandCursor }
        TapHandler {
            onTapped: root.newTabRequested()
        }
    }

    MouseArea {
        anchors.left: newTabButton.right
        anchors.leftMargin: 6
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        acceptedButtons: Qt.LeftButton
        onPressed: root.backgroundPressed()
    }
}
