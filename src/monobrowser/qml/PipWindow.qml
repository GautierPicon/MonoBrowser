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
    property bool playing: true
    property real progressRatio: 0
    property real duration: 0

    readonly property real factor: videoRect.width > 0
        ? Math.min(width / videoRect.width, height / videoRect.height)
        : 1

    signal exitRequested()
    signal minimizeRequested()
    signal closeRequested()
    signal backToPageRequested()
    signal playPauseRequested()
    signal seekRequested(real ratio)

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
        if (!view || videoRect.width <= 0)
            return
        view.width = viewport.width
        view.height = viewport.height
        view.x = -videoRect.x
        view.y = -videoRect.y
    }

    function setVideoRect(rect) {
        videoRect = Qt.rect(rect.x, rect.y, rect.width, rect.height)
        place()
    }

    function open(target, homeItem, rect) {
        view = target
        home = homeItem
        playing = true
        progressRatio = 0
        duration = 0
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

        Item {
            id: videoClip
            clip: true
            width: root.videoRect.width * root.factor
            height: root.videoRect.height * root.factor
            x: Math.round((stageHost.width - videoClip.width) / 2)
            y: Math.round((stageHost.height - videoClip.height) / 2)

            Item {
                id: stage
                width: root.videoRect.width
                height: root.videoRect.height

                transform: Scale {
                    xScale: root.factor
                    yScale: root.factor
                    origin.x: 0
                    origin.y: 0
                }
            }
        }
    }

    Item {
        id: overlay
        anchors.fill: parent

        HoverHandler { id: hover }

        Shortcut {
            sequences: ["Escape"]
            onActivated: root.closeRequested()
        }

        component ChromeButton: Rectangle {
            id: button

            property string iconName: ""
            signal tapped()

            width: 24
            height: 24
            radius: 12
            color: buttonHover.hovered ? "#4D000000" : "transparent"

            IconImage {
                anchors.centerIn: parent
                bridge: root.bridge
                iconName: button.iconName
                color: "#FFFFFF"
                size: 13
            }

            HoverHandler { id: buttonHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: button.tapped() }
        }

        Item {
            id: topBar
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

            MouseArea {
                anchors.left: leftButtons.right
                anchors.leftMargin: 4
                anchors.right: closeButton.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                onPressed: root.startSystemMove()
            }

            Row {
                id: leftButtons
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                ChromeButton {
                    iconName: "svg/pip/minus.svg"
                    onTapped: root.minimizeRequested()
                }

                ChromeButton {
                    iconName: "svg/pip/back-to-page.svg"
                    onTapped: root.backToPageRequested()
                }
            }

            Text {
                anchors.left: leftButtons.right
                anchors.leftMargin: 10
                anchors.right: closeButton.left
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                text: root.title
                elide: Text.ElideRight
                font.pixelSize: 12
                color: "#FFFFFF"
            }

            ChromeButton {
                id: closeButton
                iconName: "svg/tabs/close.svg"
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                width: 22
                height: 22
                radius: 11
                onTapped: root.closeRequested()
            }
        }

        Rectangle {
            id: playPauseButton
            width: 48
            height: 48
            radius: 24
            anchors.centerIn: parent
            color: playPauseHover.hovered ? "#CC000000" : "#99000000"
            opacity: hover.hovered || !root.playing ? 1 : 0
            visible: opacity > 0

            Behavior on opacity {
                NumberAnimation { duration: 120 }
            }

            IconImage {
                anchors.centerIn: parent
                bridge: root.bridge
                iconName: root.playing ? "svg/pip/pause.svg" : "svg/pip/play.svg"
                color: "#FFFFFF"
                size: 20
            }

            HoverHandler { id: playPauseHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: root.playPauseRequested() }
        }

        Item {
            id: seekBar
            readonly property bool active: root.width >= 300 && root.duration > 0
            readonly property real displayRatio: Math.max(0, Math.min(1,
                dragArea.dragging ? dragArea.dragRatio : root.progressRatio))

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 22
            opacity: seekBar.active && (hover.hovered || dragArea.pressed) ? 1 : 0
            visible: opacity > 0

            Behavior on opacity {
                NumberAnimation { duration: 120 }
            }

            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#00000000" }
                    GradientStop { position: 1.0; color: "#B3000000" }
                }
            }

            Rectangle {
                id: track
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                height: 3
                radius: 1.5
                color: "#4DFFFFFF"
            }

            Rectangle {
                anchors.left: track.left
                anchors.verticalCenter: track.verticalCenter
                width: track.width * seekBar.displayRatio
                height: 5
                radius: 2.5
                color: "#FFFFFF"
            }

            MouseArea {
                id: dragArea
                anchors.fill: parent
                preventStealing: true

                property bool dragging: false
                property real dragRatio: 0

                onPressed: function (mouse) { update(mouse.x) }
                onPositionChanged: function (mouse) { if (pressed) update(mouse.x) }
                onReleased: function () { dragging = false; root.progressRatio = dragRatio }
                onCanceled: dragging = false

                function update(x) {
                    var ratio = Math.max(0, Math.min(1, (x - 12) / Math.max(1, width - 24)))
                    dragRatio = ratio
                    dragging = true
                    root.seekRequested(ratio)
                }
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
