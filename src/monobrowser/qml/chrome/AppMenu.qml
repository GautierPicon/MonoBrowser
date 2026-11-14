import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import ".."

Item {
    id: root

    property var windowRef: null
    property var bridge: null
    property bool pipActive: false

    readonly property int menuPadding: 20
    readonly property int menuWidth: 200
    readonly property int menuMinHeight: 40

    implicitWidth: 28
    implicitHeight: 28

    ToolButton {
        id: button
        anchors.fill: parent
        padding: 0
        hoverEnabled: true

        background: Rectangle {
            radius: 6
            color: button.hovered ? Theme.newtabHover : "transparent"
        }

        contentItem: Item {
            IconImage {
                anchors.centerIn: parent
                bridge: root.bridge
                iconName: "menu/menu.svg"
                color: button.hovered ? Theme.textActive : Theme.iconNormal
                size: 16
            }
        }

        onClicked: rootMenu.popup(button,
                                  button.width - rootMenu.implicitWidth,
                                  button.height + 4)
    }

    Menu {
        id: rootMenu

        popupType: Popup.Window
        margins: 0
        leftInset: -root.menuPadding
        topInset: -root.menuPadding
        rightInset: -root.menuPadding
        bottomInset: -root.menuPadding
        padding: 5

        background: Item {
            implicitWidth: root.menuWidth + 2 * root.menuPadding
            implicitHeight: root.menuMinHeight + 2 * root.menuPadding

            MultiEffect {
                x: root.menuPadding
                y: root.menuPadding
                width: source.width
                height: source.height
                source: Rectangle {
                    width: rootMenu.background.width - 2 * root.menuPadding
                    height: rootMenu.background.height - 2 * root.menuPadding
                    radius: 10
                    color: Theme.menuBg
                    border.width: 1
                    border.color: Theme.menuBorder
                    visible: false
                }
                shadowEnabled: true
                shadowColor: "#000000"
                shadowOpacity: Theme.dark ? 0.45 : 0.25
                shadowBlur: 0.7
                shadowVerticalOffset: 5
            }
        }

        component Entry: MenuItem {
            id: control

            property string shortcut: ""

            implicitHeight: 26
            padding: 0
            spacing: 0

            contentItem: Item {
                implicitWidth: label.implicitWidth + 48 + shortcutLabel.implicitWidth
                implicitHeight: 26

                Text {
                    id: label
                    anchors.left: parent.left
                    anchors.leftMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: control.text
                    font.pixelSize: 13
                    color: !control.enabled ? Theme.menuTextDim
                         : (control.highlighted ? Theme.menuHoverText : Theme.menuText)
                }

                Text {
                    id: shortcutLabel
                    anchors.right: parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: control.shortcut
                    visible: text !== ""
                    font.pixelSize: 13
                    color: !control.enabled ? Theme.menuTextDim
                         : (control.highlighted ? Theme.menuHoverText : Theme.menuTextDim)
                }
            }

            background: Rectangle {
                radius: 5
                color: control.enabled && control.highlighted ? Theme.menuHover : "transparent"
            }
        }

        Entry {
            text: "New Tab"
            shortcut: "⌘T"
            onTriggered: root.windowRef.addTab()
        }
        Entry {
            text: "Reopen Closed Tab"
            shortcut: "⌘⇧T"
            enabled: root.windowRef !== null && root.windowRef.closedCount > 0
            onTriggered: root.windowRef.reopenClosedTab()
        }
        Entry {
            text: root.pipActive ? "Exit Picture in Picture" : "Picture in Picture"
            shortcut: "⌘⇧P"
            onTriggered: root.windowRef.togglePip()
        }
        Entry {
            text: "Settings"
            shortcut: "⌘,"
            onTriggered: root.windowRef.openAbout("settings")
        }
        Entry {
            text: "About MonoBrowser"
            onTriggered: root.windowRef.openAbout("version")
        }
        MenuSeparator {
            padding: 0
            horizontalPadding: 8
            verticalPadding: 5

            contentItem: Rectangle {
                implicitHeight: 1
                color: Theme.menuBorder
            }
        }
        Entry {
            text: "Quit MonoBrowser"
            shortcut: "⌘Q"
            onTriggered: root.windowRef.close()
        }
    }
}
