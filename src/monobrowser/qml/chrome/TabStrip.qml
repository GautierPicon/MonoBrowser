pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: root

    property var tabModel: null
    property int currentIndex: -1
    property var bridge: null
    property int dropIndex: -1

    signal tabClicked(int index)
    signal tabClosed(int index)
    signal tabMoved(int from, int to)
    signal newTabRequested()
    signal backgroundPressed()
    signal backgroundDoubleClicked()

    implicitHeight: 40

    readonly property int newTabWidth: 34
    readonly property int tabCount: root.tabModel ? root.tabModel.count : 0
    readonly property int tabWidth: root.tabCount > 0
        ? Math.max(72, Math.min(240, Math.floor((root.width - root.newTabWidth) / root.tabCount)))
        : 240
    readonly property int stripWidth: root.tabCount * root.tabWidth + root.newTabWidth

    onCurrentIndexChanged: if (root.currentIndex >= 0) flick.ensureVisible(root.currentIndex)
    onStripWidthChanged: flick.contentX = Math.max(0, Math.min(flick.contentX, Math.max(0, stripWidth - flick.width)))

    function dropIndexFor(delegate, contentX) {
        var width = delegate.width
        var center = delegate.x + contentX + width / 2
        root.dropIndex = Math.max(0, Math.min(root.tabCount - 1, Math.floor(center / root.tabWidth)))
    }

    MouseArea {
        id: backgroundArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton

        property point pressPoint
        property bool moving: false

        onPressed: function (mouse) {
            backgroundArea.pressPoint = Qt.point(mouse.x, mouse.y)
            backgroundArea.moving = false
        }
        onPositionChanged: function (mouse) {
            if (!pressed || backgroundArea.moving)
                return
            if (Math.abs(mouse.x - backgroundArea.pressPoint.x) > 4
                    || Math.abs(mouse.y - backgroundArea.pressPoint.y) > 4) {
                backgroundArea.moving = true
                root.backgroundPressed()
            }
        }
        onReleased: backgroundArea.moving = false
        onDoubleClicked: root.backgroundDoubleClicked()
    }

    Flickable {
        id: flick

        anchors.fill: parent
        clip: true
        interactive: false
        boundsBehavior: Flickable.StopAtBounds
        contentWidth: stripRow.width
        contentHeight: height

        function ensureVisible(index) {
            var start = index * root.tabWidth
            var end = start + root.tabWidth
            if (start < contentX)
                contentX = start
            else if (end > contentX + width)
                contentX = end - width
        }

        WheelHandler {
            id: wheel

            onWheel: function (event) {
                var delta = event.angleDelta.y !== 0 ? event.angleDelta.y : event.pixelDelta.y
                if (Math.abs(event.angleDelta.x) > Math.abs(delta))
                    delta = event.angleDelta.x
                var step = Math.abs(delta) >= 60 ? delta / 120 * 60 : delta
                var maxX = Math.max(0, flick.contentWidth - flick.width)
                flick.contentX = Math.max(0, Math.min(maxX, flick.contentX - step))
            }
        }

        Row {
            id: stripRow

            height: flick.height
            spacing: 0

            Repeater {
                model: root.tabModel

                delegate: Item {
                    id: tabDelegate

                    required property int index
                    required property string title
                    required property string favicon
                    required property string url
                    required property bool loading

                    readonly property bool isCurrent: index === root.currentIndex

                    width: root.tabWidth
                    height: 38
                    z: dragHandler.active ? 100 : 0

                    Item {
                        id: contentItem

                        width: parent.width
                        height: parent.height
                        opacity: dragHandler.active ? 0.85 : 1.0
                        x: dragHandler.active
                            ? Math.max(-tabDelegate.x,
                                       Math.min(stripRow.width - root.newTabWidth - tabDelegate.x - width,
                                                dragHandler.translation.x))
                            : 0

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

                        Item {
                            id: iconSlot

                            width: 16
                            height: 16
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter

                            IconImage {
                                id: spinner

                                visible: tabDelegate.loading
                                anchors.centerIn: parent
                                bridge: root.bridge
                                iconName: "tabs/spinner.svg"
                                color: Theme.textInactive
                                size: 16
                
                                RotationAnimator on rotation {
                                    from: 0
                                    to: 360
                                    duration: 900
                                    loops: Animation.Infinite
                                    running: tabDelegate.loading
                                }
                            }

                            Image {
                                visible: !tabDelegate.loading && tabDelegate.favicon !== ""
                                width: 16
                                height: 16
                                anchors.centerIn: parent
                                source: tabDelegate.favicon
                                asynchronous: true
                                fillMode: Image.PreserveAspectFit
                            }

                            IconImage {
                                visible: !tabDelegate.loading && tabDelegate.favicon === ""
                                anchors.centerIn: parent
                                bridge: root.bridge
                                iconName: "globe.svg"
                                color: Theme.textInactive
                                size: 16
                            }
                        }

                        Text {
                            id: label

                            anchors.left: iconSlot.right
                            anchors.leftMargin: 8
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

                            IconImage {
                                anchors.centerIn: parent
                                bridge: root.bridge
                                iconName: "tabs/close.svg"
                                color: Theme.closeGlyph
                                size: 14
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

                        TapHandler {
                            acceptedButtons: Qt.MiddleButton
                            onTapped: root.tabClosed(tabDelegate.index)
                        }

                        ToolTip.text: (tabDelegate.title !== "" ? tabDelegate.title : "New Tab") + "\n" + tabDelegate.url
                        ToolTip.visible: hover.hovered && !dragHandler.active
                        ToolTip.delay: 600
                        ToolTip.timeout: 8000

                        DragHandler {
                            id: dragHandler

                            xAxis.enabled: true
                            yAxis.enabled: false
                            target: null

                            onTranslationChanged: root.dropIndexFor(tabDelegate, contentItem.x)

                            onActiveChanged: {
                                if (dragHandler.active) {
                                    root.dropIndex = tabDelegate.index
                                    return
                                }
                                var from = tabDelegate.index
                                var to = root.dropIndex
                                root.dropIndex = -1
                                if (to >= 0 && to !== from)
                                    root.tabMoved(from, to)
                            }
                        }
                    }
                }
            }

            Item {
                width: root.newTabWidth
                height: stripRow.height

                Rectangle {
                    id: newTabButton

                    width: 28
                    height: 28
                    radius: 14
                    anchors.centerIn: parent
                    color: newTabHover.hovered ? Theme.newtabHover : "transparent"

                    IconImage {
                        anchors.centerIn: parent
                        bridge: root.bridge
                        iconName: "tabs/new.svg"
                        color: newTabHover.hovered ? Theme.textActive : Theme.textInactive
                        size: 16
                    }

                    HoverHandler { id: newTabHover; cursorShape: Qt.PointingHandCursor }
                    TapHandler {
                        onTapped: root.newTabRequested()
                    }
                }
            }
        }

        Rectangle {
            id: dropIndicator

            visible: root.dropIndex >= 0
            x: root.dropIndex * root.tabWidth
            y: 4
            width: 3
            height: 32
            radius: 1.5
            color: Theme.progress
        }
    }
}
