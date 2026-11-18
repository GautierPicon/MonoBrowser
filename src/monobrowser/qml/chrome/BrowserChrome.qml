import QtQuick
import QtQuick.Controls
import ".."

Item {
    id: root

    property ListModel tabModel: null
    property int currentIndex: -1
    property string address: ""
    property var bridge: null
    property var windowRef: null
    property bool pipActive: false
    property bool pipDetached: false
    property bool canPip: false
    property var pipSnapshot: null
    property rect pipVideoFrac: Qt.rect(0, 0, 1, 1)
    property var swipeView: null

    readonly property Item contentArea: contentAreaItem
    readonly property var navBar: navBarItem
    readonly property var loadingBar: loadingBarItem
    readonly property var linkBar: linkBarItem
    readonly property var findBar: findBarItem
    readonly property var zoomHud: zoomHudItem

    signal tabClicked(int index)
    signal tabClosed(int index)
    signal tabMoved(int from, int to)
    signal tabMuteToggled(int index)
    signal newTabRequested()
    signal backgroundPressed()
    signal backgroundDoubleClicked()
    signal addressSubmitted(string text)
    signal backRequested()
    signal forwardRequested()
    signal reloadRequested()
    signal stopRequested()
    signal pipRequested()
    signal faviconError(int index)

    Column {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: tabstripRow
            width: parent.width
            height: 40
            color: Theme.tabstripBg

            TabStrip {
                id: tabstrip
                anchors.left: parent.left
                anchors.leftMargin: 78
                anchors.right: appMenu.left
                anchors.rightMargin: 4
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                tabModel: root.tabModel
                currentIndex: root.currentIndex
                bridge: root.bridge
                onTabClicked: function (index) { root.tabClicked(index) }
                onTabClosed: function (index) { root.tabClosed(index) }
                onTabMoved: function (from, to) { root.tabMoved(from, to) }
                onTabMuteToggled: function (index) { root.tabMuteToggled(index) }
                onNewTabRequested: root.newTabRequested()
                onFaviconError: function (index) { root.faviconError(index) }
                onBackgroundPressed: root.backgroundPressed()
                onBackgroundDoubleClicked: root.backgroundDoubleClicked()
            }

            AppMenu {
                id: appMenu
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                windowRef: root.windowRef
                bridge: root.bridge
                pipActive: root.pipActive
            }
        }

        Rectangle {
            id: toolbarRow
            width: parent.width
            height: 38
            color: Theme.toolbarBg

            Toolbar {
                id: navBarItem
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                address: root.address
                bridge: root.bridge
                canPip: root.canPip
                pipActive: root.pipActive
                onBackRequested: root.backRequested()
                onForwardRequested: root.forwardRequested()
                onReloadRequested: root.reloadRequested()
                onStopRequested: root.stopRequested()
                onPipRequested: root.pipRequested()
                onAddressSubmitted: function (text) { root.addressSubmitted(text) }
            }
        }

        ProgressBar {
            id: loadingBarItem
            visible: false
            width: parent.width
            implicitHeight: 3
            indeterminate: false
            from: 0
            to: 1
            background: Rectangle { color: "transparent" }
            contentItem: Rectangle {
                color: Theme.progress
                width: loadingBarItem.visualPosition * loadingBarItem.width
                height: 3
            }
        }

        Item {
            id: contentAreaItem
            width: parent.width
            height: parent.height - tabstripRow.height - toolbarRow.height - loadingBarItem.implicitHeight
            clip: true

            Item {
                anchors.fill: parent
                visible: root.pipDetached

                Image {
                    anchors.fill: parent
                    visible: root.pipSnapshot !== null && String(root.pipSnapshot) !== ""
                    source: root.pipSnapshot ? String(root.pipSnapshot) : ""
                    fillMode: Image.Stretch
                }

                Rectangle {
                    anchors.fill: parent
                    visible: root.pipSnapshot !== null && String(root.pipSnapshot) !== ""
                    color: "#40000000"
                }

                Rectangle {
                    x: parent.width * root.pipVideoFrac.x
                    y: parent.height * root.pipVideoFrac.y
                    width: Math.max(0, parent.width * root.pipVideoFrac.width)
                    height: Math.max(0, parent.height * root.pipVideoFrac.height)
                    color: "#000000"

                    IconImage {
                        anchors.centerIn: parent
                        visible: parent.width >= 90 && parent.height >= 56
                        bridge: root.bridge
                        iconName: "svg/pip/pip.svg"
                        color: "#FFFFFF"
                        size: 34
                    }
                }
            }

            HistorySwipe {
                anchors.fill: parent
                z: 50
                view: root.swipeView
                bridge: root.bridge
                swipeEnabled: !root.pipActive && root.swipeView !== null
            }

            FindBar {
                id: findBarItem
                anchors.top: parent.top
                anchors.topMargin: 10
                anchors.right: parent.right
                anchors.rightMargin: 12
                windowRef: root.windowRef
            }

            Rectangle {
                id: zoomHudItem
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 36
                width: hudLabel.implicitWidth + 28
                height: 30
                radius: 15
                z: 60
                opacity: 0
                visible: opacity > 0
                color: Theme.menuBg
                border.width: 1
                border.color: Theme.menuBorder

                Behavior on opacity {
                    NumberAnimation { duration: 150 }
                }

                Text {
                    id: hudLabel
                    anchors.centerIn: parent
                    text: "100%"
                    font.pixelSize: 13
                    color: Theme.menuText
                }

                Timer {
                    id: hudTimer
                    interval: 1000
                    onTriggered: zoomHudItem.opacity = 0
                }

                function show(percent) {
                    hudLabel.text = percent + "%"
                    zoomHudItem.opacity = 1
                    hudTimer.restart()
                }
            }
        }
    }

    LinkBar {
        id: linkBarItem
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 8
        anchors.bottomMargin: 8
    }
}
