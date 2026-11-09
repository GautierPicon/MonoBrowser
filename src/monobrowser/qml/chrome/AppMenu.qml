import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import ".."

Item {
    id: root

    property var windowRef: null

    implicitWidth: 28
    implicitHeight: 28

    ToolButton {
        id: button
        anchors.fill: parent
        text: "☰"
        padding: 0
        hoverEnabled: true

        background: Rectangle {
            radius: 6
            color: button.hovered ? Theme.newtabHover : "transparent"
        }

        contentItem: Text {
            text: button.text
            font.pixelSize: 15
            color: button.hovered ? Theme.textActive : Theme.iconNormal
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        onClicked: rootMenu.popup(button,
                                  button.width - rootMenu.implicitWidth,
                                  button.height + 4)
    }

    Menu {
        id: rootMenu

        popupType: Popup.Window
        margins: 0
        leftInset: -20
        topInset: -20
        rightInset: -20
        bottomInset: -20
        padding: 5

        background: Item {
            implicitWidth: 200 - rootMenu.leftInset - rootMenu.rightInset
            implicitHeight: 40 - rootMenu.topInset - rootMenu.bottomInset

            MultiEffect {
                x: -rootMenu.leftInset
                y: -rootMenu.topInset
                width: source.width
                height: source.height
                source: Rectangle {
                    width: rootMenu.background.width + rootMenu.leftInset + rootMenu.rightInset
                    height: rootMenu.background.height + rootMenu.topInset + rootMenu.bottomInset
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
