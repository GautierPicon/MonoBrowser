import QtQuick
import QtQuick.Controls

Row {
    id: root

    property bool canGoBack: false
    property bool canGoForward: false
    property bool loading: false
    property string address: ""

    signal backRequested()
    signal forwardRequested()
    signal reloadRequested()
    signal stopRequested()
    signal addressSubmitted(string text)

    spacing: 2

    function focusAddress() {
        addressInput.forceActiveFocus()
        addressInput.selectAll()
    }

    function refreshHistory(back, forward) {
        root.canGoBack = back
        root.canGoForward = forward
    }

    NavButton {
        enabled: root.canGoBack
        glyph: "←"
        tip: "Back"
        onClicked: root.backRequested()
    }

    NavButton {
        enabled: root.canGoForward
        glyph: "→"
        tip: "Forward"
        onClicked: root.forwardRequested()
    }

    NavButton {
        glyph: root.loading ? "✕" : "⟳"
        tip: root.loading ? "Stop" : "Reload"
        onClicked: root.loading ? root.stopRequested() : root.reloadRequested()
    }

    Rectangle {
        id: addressBg
        width: parent.width - root.children.length * 32
        height: 26
        anchors.verticalCenter: parent.verticalCenter
        radius: 8
        color: Theme.urlbarBg
        border.width: 1
        border.color: addressInput.activeFocus ? Theme.urlbarFocus : Theme.urlbarBorder

        Behavior on border.color {
            ColorAnimation { duration: 120 }
        }

        TextField {
            id: addressInput
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            verticalAlignment: TextInput.AlignVCenter
            background: null
            color: Theme.textActive
            placeholderText: "Search or enter address"
            placeholderTextColor: Theme.textInactive
            selectionColor: Theme.urlbarFocus
            selectedTextColor: Theme.textActive
            font.pixelSize: 13
            text: root.address
            selectByMouse: true

            onAccepted: root.addressSubmitted(text)
            onActiveFocusChanged: {
                if (activeFocus)
                    selectAll()
            }

            Keys.onEscapePressed: {
                text = root.address
                focus = false
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                onPressed: addressInput.selectAll()
            }
        }
    }
}
