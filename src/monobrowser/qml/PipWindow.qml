pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
import "chrome"

Window {
    id: root

    property var bridge: null
    property var view: null
    property Item home: null
    property size viewport: Qt.size(0, 0)
    property rect videoRect: Qt.rect(0, 0, 0, 0)

    readonly property real factor: videoRect.width > 0
        ? Math.min(width / videoRect.width, height / videoRect.height)
        : 1

    signal exitRequested()

    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "#000000"
    minimumWidth: 160
    minimumHeight: 90
    title: "Picture in Picture"

    onWidthChanged: place()
    onHeightChanged: place()
    onVisibleChanged: {
        if (!visible && view)
            root.exitRequested()
    }

    function place() {
        if (!view || videoRect.width <= 0 || stage.width <= 0)
            return
        view.width = viewport.width
        view.height = viewport.height
        view.x = (stage.width - videoRect.width) / 2 - videoRect.x
        view.y = (stage.height - videoRect.height) / 2 - videoRect.y
    }

    function setVideoRect(rect) {
        videoRect = Qt.rect(rect.x, rect.y, rect.width, rect.height)
        place()
    }

    function open(target, homeItem, rect) {
        view = target
        home = homeItem
        viewport = Qt.size(Math.max(1, target.width), Math.max(1, target.height))
        target.anchors.fill = undefined
        target.parent = stage
        setVideoRect(rect)

        width = Math.min(640, Math.max(320, Math.round(rect.width)))
        height = Math.max(160, Math.round(width * rect.height / rect.width))
        x = Math.max(24, Screen.desktopAvailableWidth - width - 24)
        y = Math.max(24, Screen.desktopAvailableHeight - height - 24)

        place()
        visible = true
        requestActivate()
        target.forceActiveFocus()
    }

    function release() {
        if (!view)
            return
        var target = view
        var host = home
        view = null
        home = null
        videoRect = Qt.rect(0, 0, 0, 0)
        visible = false
        target.parent = host
        target.x = 0
        target.y = 0
        target.anchors.fill = host
    }

    Item {
        id: stageHost
        anchors.fill: parent
        clip: true

        Item {
            id: stage
            width: root.width / root.factor
            height: root.height / root.factor
            transform: Scale { xScale: root.factor; yScale: root.factor }
        }
    }

    Item {
        id: overlay
        anchors.fill: parent

        HoverHandler { id: hover }

        Shortcut {
            sequences: ["Escape"]
            onActivated: root.exitRequested()
        }

        Item {
            id: titleBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 34
            opacity: hover.hovered ? 1 : 0
            visible: opacity > 0

            Behavior on opacity {
                NumberAnimation { duration: 120 }
            }

            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#B3000000" }
                    GradientStop { position: 1.0; color: "#00000000" }
                }
            }

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: closeButton.left
                anchors.rightMargin: 8
                text: root.title
                elide: Text.ElideRight
                font.pixelSize: 12
                color: "#FFFFFF"
            }

            MouseArea {
                anchors.left: parent.left
                anchors.right: closeButton.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                onPressed: root.startSystemMove()
            }

            Rectangle {
                id: closeButton
                width: 22
                height: 22
                radius: 11
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                color: closeHover.hovered ? "#4D000000" : "transparent"

                IconImage {
                    anchors.centerIn: parent
                    bridge: root.bridge
                    iconName: "tabs/close.svg"
                    color: "#FFFFFF"
                    size: 12
                }

                HoverHandler { id: closeHover; cursorShape: Qt.PointingHandCursor }
                TapHandler { onTapped: root.exitRequested() }
            }
        }

        component Handle: MouseArea {
            property int edges: Qt.LeftEdge
            property int shape: Qt.SizeHorCursor

            hoverEnabled: true
            cursorShape: shape
            onPressed: root.startSystemResize(edges)
        }

        Handle {
            edges: Qt.LeftEdge
            shape: Qt.SizeHorCursor
            width: 6
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }
        Handle {
            edges: Qt.RightEdge
            shape: Qt.SizeHorCursor
            width: 6
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }
        Handle {
            edges: Qt.TopEdge
            shape: Qt.SizeVerCursor
            height: 6
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
        }
        Handle {
            edges: Qt.BottomEdge
            shape: Qt.SizeVerCursor
            height: 6
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
        }
        Handle {
            edges: Qt.LeftEdge | Qt.TopEdge
            shape: Qt.SizeFDiagCursor
            width: 14
            height: 14
            anchors.left: parent.left
            anchors.top: parent.top
        }
        Handle {
            edges: Qt.RightEdge | Qt.BottomEdge
            shape: Qt.SizeFDiagCursor
            width: 14
            height: 14
            anchors.right: parent.right
            anchors.bottom: parent.bottom
        }
        Handle {
            edges: Qt.RightEdge | Qt.TopEdge
            shape: Qt.SizeBDiagCursor
            width: 14
            height: 14
            anchors.right: parent.right
            anchors.top: parent.top
        }
        Handle {
            edges: Qt.LeftEdge | Qt.BottomEdge
            shape: Qt.SizeBDiagCursor
            width: 14
            height: 14
            anchors.left: parent.left
            anchors.bottom: parent.bottom
        }
    }
}
