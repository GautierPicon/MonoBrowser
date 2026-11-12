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

    readonly property Item contentArea: contentAreaItem
    readonly property var navBar: navBarItem
    readonly property var loadingBar: loadingBarItem
    readonly property var linkBar: linkBarItem

    signal tabClicked(int index)
    signal tabClosed(int index)
    signal newTabRequested()
    signal backgroundPressed()
    signal backgroundDoubleClicked()
    signal addressSubmitted(string text)
    signal backRequested()
    signal forwardRequested()
    signal reloadRequested()
    signal stopRequested()

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
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                tabModel: root.tabModel
                currentIndex: root.currentIndex
                bridge: root.bridge
                onTabClicked: function (index) { root.tabClicked(index) }
                onTabClosed: function (index) { root.tabClosed(index) }
                onNewTabRequested: root.newTabRequested()
                onBackgroundPressed: root.backgroundPressed()
                onBackgroundDoubleClicked: root.backgroundDoubleClicked()
            }

            AppMenu {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                windowRef: root.windowRef
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
                onBackRequested: root.backRequested()
                onForwardRequested: root.forwardRequested()
                onReloadRequested: root.reloadRequested()
                onStopRequested: root.stopRequested()
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
