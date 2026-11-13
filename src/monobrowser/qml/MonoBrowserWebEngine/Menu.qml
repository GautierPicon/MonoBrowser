import QtQuick
import QtQuick.Controls as C
import QtQuick.Effects
import ".."

C.Menu {
    id: root

    signal done()

    readonly property int shadowPadding: 20
    readonly property int menuWidth: 200
    readonly property int menuMinHeight: 40

    popupType: C.Popup.Window
    margins: 0
    leftInset: -root.shadowPadding
    topInset: -root.shadowPadding
    rightInset: -root.shadowPadding
    bottomInset: -root.shadowPadding
    padding: 5

    onAboutToHide: doneTimer.start()

    Timer {
        id: doneTimer
        interval: 100
        onTriggered: root.done()
    }

    background: Item {
        implicitWidth: root.menuWidth + 2 * root.shadowPadding
        implicitHeight: root.menuMinHeight + 2 * root.shadowPadding

        MultiEffect {
            x: root.shadowPadding
            y: root.shadowPadding
            width: source.width
            height: source.height
            source: Rectangle {
                width: root.background.width - 2 * root.shadowPadding
                height: root.background.height - 2 * root.shadowPadding
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
}
