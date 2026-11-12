import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

RowLayout {
    id: root

    property bool canGoBack: false
    property bool canGoForward: false
    property bool loading: false
    property string address: ""
    property bool editing: false
    property bool certificateError: false
    property var bridge: null
    property bool canPip: false
    property bool pipActive: false

    readonly property bool secure: !certificateError && address.indexOf("https://") === 0
    readonly property bool insecure: certificateError || address.indexOf("http://") === 0

    signal backRequested()
    signal forwardRequested()
    signal reloadRequested()
    signal stopRequested()
    signal addressSubmitted(string text)
    signal pipRequested()

    spacing: 2

    function focusAddress() {
        addressInput.forceActiveFocus()
        addressInput.selectAll()
    }

    function refreshHistory(back, forward) {
        root.canGoBack = back
        root.canGoForward = forward
    }

    function displayAddress(value) {
        var text = String(value)
        if (text.indexOf("https://") === 0)
            text = text.substring(8)
        else if (text.indexOf("http://") === 0)
            text = text.substring(7)
        else
            return text
        if (text.indexOf("www.") === 0)
            text = text.substring(4)
        return text
    }

    onAddressChanged: {
        if (!addressInput.activeFocus)
            addressInput.text = displayAddress(root.address)
        else if (!root.editing)
            addressInput.text = root.address
    }

    NavButton {
        enabled: root.canGoBack
        iconName: "nav/back.svg"
        bridge: root.bridge
        tip: "Back"
        onClicked: root.backRequested()
    }

    NavButton {
        enabled: root.canGoForward
        iconName: "nav/forward.svg"
        bridge: root.bridge
        tip: "Forward"
        onClicked: root.forwardRequested()
    }

    NavButton {
        iconName: root.loading ? "" : "nav/reload.svg"
        glyph: root.loading ? "✕" : ""
        bridge: root.bridge
        tip: root.loading ? "Stop" : "Reload"
        onClicked: root.loading ? root.stopRequested() : root.reloadRequested()
    }

    NavButton {
        visible: root.canPip || root.pipActive
        iconName: "pip/pip.svg"
        bridge: root.bridge
        tip: root.pipActive ? "Exit Picture in Picture" : "Picture in Picture"
        onClicked: root.pipRequested()
    }

    Rectangle {
        id: addressBg
        Layout.fillWidth: true
        Layout.preferredHeight: 26
        Layout.alignment: Qt.AlignVCenter
        radius: 8
        color: Theme.urlbarBg
        border.width: 1
        border.color: addressInput.activeFocus ? Theme.urlbarFocus : Theme.urlbarBorder

        Behavior on border.color {
            ColorAnimation { duration: 120 }
        }

        IconImage {
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            visible: root.secure
            bridge: root.bridge
            iconName: "lock/lock.svg"
            color: Theme.textInactive
            size: 14
        }

        IconImage {
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            visible: root.insecure
            bridge: root.bridge
            iconName: "lock/lock-open.svg"
            color: "#E00000"
            size: 14
        }

        TextField {
            id: addressInput
            anchors.fill: parent
            anchors.leftMargin: 26
            anchors.rightMargin: 10
            verticalAlignment: TextInput.AlignVCenter
            background: null
            color: Theme.textActive
            placeholderText: "Search or enter address"
            placeholderTextColor: Theme.textInactive
            selectionColor: Theme.urlbarFocus
            selectedTextColor: Theme.textActive
            font.pixelSize: 13
            text: root.displayAddress(root.address)
            selectByMouse: true

            onTextEdited: root.editing = true

            onAccepted: {
                root.editing = false
                root.addressSubmitted(text)
            }

            onActiveFocusChanged: {
                if (activeFocus) {
                    root.editing = false
                    text = root.address
                    selectAll()
                } else {
                    root.editing = false
                    text = root.displayAddress(root.address)
                }
            }

            Keys.onEscapePressed: {
                root.editing = false
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
