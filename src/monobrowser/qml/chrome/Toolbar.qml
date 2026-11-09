import QtQuick
import QtQuick.Controls
import ".."

Row {
    id: root

    property bool canGoBack: false
    property bool canGoForward: false
    property bool loading: false
    property string address: ""
    property bool editing: false
    property bool certificateError: false
    property url secureIcon: ""
    property url insecureIcon: ""

    readonly property bool secure: !certificateError && address.indexOf("https://") === 0
    readonly property bool insecure: certificateError || address.indexOf("http://") === 0

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

        Item {
            id: securityIcon
            width: 13
            height: 14
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            visible: root.secure || root.insecure

            Image {
                anchors.fill: parent
                visible: root.secure
                source: root.secureIcon
                sourceSize: Qt.size(13, 14)
                fillMode: Image.PreserveAspectFit
            }

            Image {
                anchors.fill: parent
                visible: root.insecure
                source: root.insecureIcon
                sourceSize: Qt.size(13, 14)
                fillMode: Image.PreserveAspectFit
            }
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
