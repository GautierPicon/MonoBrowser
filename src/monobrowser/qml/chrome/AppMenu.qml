import QtQuick
import QtQuick.Controls

Item {
    id: root

    property var windowRef: null

    implicitWidth: 28
    implicitHeight: 28

    ToolButton {
        id: button
        anchors.fill: parent
        text: "☰"
        font.pixelSize: 15
        padding: 0
        onClicked: rootMenu.popup(button, 0, button.height + 2)
    }

    Menu {
        id: rootMenu

        MenuItem {
            text: "New Tab"
            onTriggered: windowRef.addTab()
        }
        MenuItem {
            text: "Settings"
            onTriggered: windowRef.openAbout("settings")
        }
        MenuItem {
            text: "About MonoBrowser"
            onTriggered: windowRef.openAbout("version")
        }
        MenuSeparator {}
        MenuItem {
            text: "Quit MonoBrowser"
            onTriggered: windowRef.close()
        }
    }
}