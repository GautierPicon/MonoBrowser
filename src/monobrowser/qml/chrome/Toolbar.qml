pragma ComponentBehavior: Bound
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
    property bool completeOnFocus: true
    property int suggestLimit: 8
    property string typedText: ""

    readonly property bool secure: !certificateError && address.indexOf("https://") === 0
    readonly property bool insecure: certificateError || address.indexOf("http://") === 0
    readonly property bool suggestOpen: addressInput.activeFocus && suggestModel.count > 0

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

    function clearSuggestions() {
        suggestTimer.stop()
        searchDebounce.stop()
        localModel.clear()
        searchModel.clear()
        suggestModel.clear()
    }

    function refreshSuggestions() {
        if (!root.bridge || addressInput.text.trim() === "") {
            root.clearSuggestions()
            return
        }
        var matches = root.bridge.suggestMatches(addressInput.text.trim(), root.suggestLimit)
        localModel.clear()
        for (var i = 0; i < matches.length; ++i) {
            var match = matches[i]
            localModel.append({
                url: String(match.url),
                title: String(match.title)
            })
        }
        root.rebuildSuggestions()
    }

    function requestSearchSuggestions() {
        if (!root.bridge || !root.bridge.suggestionsEnabled
                || addressInput.text.trim() === "")
            return
        root.bridge.requestSuggestions(addressInput.text.trim())
    }

    function rebuildSuggestions() {
        var selected = ""
        var previous = suggestView.currentIndex
        if (previous >= 0 && previous < suggestModel.count) {
            var current = suggestModel.get(previous)
            if (!current.header)
                selected = current.query !== "" ? current.query : current.url
        }
        suggestModel.clear()
        for (var i = 0; i < localModel.count; ++i) {
            var local = localModel.get(i)
            suggestModel.append({
                url: local.url,
                title: local.title,
                query: "",
                header: false
            })
        }
        if (searchModel.count > 0) {
            suggestModel.append({
                url: "",
                title: "Search suggestions",
                query: "",
                header: true
            })
            for (var j = 0; j < searchModel.count; ++j) {
                var value = searchModel.get(j).value
                suggestModel.append({
                    url: "Search with DuckDuckGo",
                    title: value,
                    query: value,
                    header: false
                })
            }
        }
        var restored = -1
        var first = -1
        for (var k = 0; k < suggestModel.count; ++k) {
            var item = suggestModel.get(k)
            if (item.header)
                continue
            if (first < 0)
                first = k
            if ((item.query !== "" ? item.query : item.url) === selected)
                restored = k
        }
        suggestView.currentIndex = restored >= 0 ? restored : first
    }

    function acceptSuggestion(index, navigate) {
        if (index < 0 || index >= suggestModel.count)
            return
        var item = suggestModel.get(index)
        if (item.header)
            return
        var target = item.query !== "" ? item.query : item.url
        addressInput.text = target
        addressInput.cursorPosition = target.length
        addressInput.deselect()
        root.editing = false
        root.clearSuggestions()
        if (navigate)
            root.addressSubmitted(target)
    }

    onAddressChanged: {
        root.clearSuggestions()
        if (!addressInput.activeFocus)
            addressInput.text = displayAddress(root.address)
        else if (!root.editing)
            addressInput.text = root.address
    }

    Timer {
        id: suggestTimer
        interval: 120
        repeat: false
        onTriggered: root.refreshSuggestions()
    }

    Timer {
        id: searchDebounce
        interval: 180
        repeat: false
        onTriggered: root.requestSearchSuggestions()
    }

    ListModel { id: localModel }
    ListModel { id: searchModel }

    Connections {
        target: root.bridge
        ignoreUnknownSignals: true

        function onSuggestionsReady(query, values) {
            if (query !== addressInput.text.trim() || !addressInput.activeFocus)
                return
            searchModel.clear()
            for (var i = 0; i < values.length; ++i)
                searchModel.append({ value: values[i] })
            root.rebuildSuggestions()
        }

        function onSuggestionsEnabledChanged() {
            searchModel.clear()
            root.rebuildSuggestions()
        }

        function onSearchEngineChanged() {
            searchModel.clear()
            searchDebounce.stop()
            root.rebuildSuggestions()
        }
    }

    NavButton {
        enabled: root.canGoBack
        iconName: "svg/nav/back.svg"
        bridge: root.bridge
        tip: "Back"
        onClicked: root.backRequested()
    }

    NavButton {
        enabled: root.canGoForward
        iconName: "svg/nav/forward.svg"
        bridge: root.bridge
        tip: "Forward"
        onClicked: root.forwardRequested()
    }

    NavButton {
        iconName: root.loading ? "" : "svg/nav/reload.svg"
        glyph: root.loading ? "✕" : ""
        bridge: root.bridge
        tip: root.loading ? "Stop" : "Reload"
        onClicked: root.loading ? root.stopRequested() : root.reloadRequested()
    }

    NavButton {
        visible: root.canPip || root.pipActive
        iconName: "svg/pip/pip.svg"
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
            iconName: "svg/lock/lock.svg"
            color: Theme.textInactive
            size: 14
        }

        IconImage {
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            visible: root.insecure
            bridge: root.bridge
            iconName: "svg/lock/lock-open.svg"
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

            onTextEdited: {
                root.editing = true
                root.typedText = text
                if (text.trim() === "")
                    root.clearSuggestions()
                else {
                    suggestTimer.restart()
                    searchDebounce.restart()
                }
            }

            onAccepted: {
                root.editing = false
                if (root.suggestOpen && suggestView.currentIndex >= 0) {
                    root.acceptSuggestion(suggestView.currentIndex, true)
                    return
                }
                root.clearSuggestions()
                root.addressSubmitted(text)
            }

            onActiveFocusChanged: {
                if (activeFocus) {
                    root.editing = false
                    text = root.address
                    root.typedText = text
                    selectAll()
                    if (root.completeOnFocus && text.trim() !== "") {
                        root.refreshSuggestions()
                        searchDebounce.restart()
                    }
                } else {
                    root.editing = false
                    root.clearSuggestions()
                    text = root.displayAddress(root.address)
                }
            }

            Keys.onUpPressed: function (event) {
                if (!root.suggestOpen)
                    return
                event.accepted = true
                var index = suggestView.currentIndex - 1
                while (index >= 0 && suggestModel.get(index).header)
                    --index
                suggestView.currentIndex = Math.max(0, index)
            }

            Keys.onDownPressed: function (event) {
                if (!root.suggestOpen)
                    return
                event.accepted = true
                var index = suggestView.currentIndex + 1
                while (index < suggestModel.count && suggestModel.get(index).header)
                    ++index
                suggestView.currentIndex = Math.min(suggestModel.count - 1, index)
            }

            Keys.onTabPressed: function (event) {
                if (!root.suggestOpen || suggestView.currentIndex < 0)
                    return
                event.accepted = true
                root.acceptSuggestion(suggestView.currentIndex, false)
            }

            Keys.onEscapePressed: function (event) {
                event.accepted = true
                if (root.suggestOpen) {
                    root.clearSuggestions()
                    addressInput.text = root.typedText
                    addressInput.cursorPosition = root.typedText.length
                    return
                }
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

        Rectangle {
            id: suggestPopup
            anchors.top: addressBg.bottom
            anchors.topMargin: 3
            anchors.left: addressBg.left
            anchors.right: addressBg.right
            height: Math.min(suggestView.contentHeight + 2, 320)
            visible: root.suggestOpen
            z: 10
            radius: 8
            color: Theme.menuBg
            border.width: 1
            border.color: Theme.menuBorder

            ListView {
                id: suggestView
                anchors.fill: parent
                anchors.margins: 1
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: ListModel { id: suggestModel }

                delegate: Item {
                    id: row
                    required property int index
                    required property string title
                    required property string url
                    required property string query
                    required property bool header

                    width: suggestView.width
                    height: row.header ? 24 : 32

                    Rectangle {
                        anchors.fill: parent
                        radius: 4
                        color: !row.header && suggestView.currentIndex === row.index ? Theme.menuHover : "transparent"
                    }

                    Row {
                        anchors.left: parent.left
                        anchors.leftMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 6
                        visible: row.header

                        IconImage {
                            bridge: root.bridge
                            iconName: "svg/search.svg"
                            color: Theme.menuTextDim
                            size: 14
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: row.title
                            color: Theme.menuTextDim
                            font.pixelSize: 11
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    Column {
                        anchors.left: parent.left
                        anchors.leftMargin: 10
                        anchors.right: parent.right
                        anchors.rightMargin: 10
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 1
                        visible: !row.header

                        Text {
                            width: parent.width
                            text: row.title
                            color: suggestView.currentIndex === row.index ? Theme.menuHoverText : Theme.menuText
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }

                        Text {
                            width: parent.width
                            text: row.url
                            color: suggestView.currentIndex === row.index ? Theme.menuHoverText : Theme.menuTextDim
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        enabled: !row.header
                        onPressed: suggestView.currentIndex = row.index
                        onClicked: root.acceptSuggestion(row.index, true)
                    }
                }
            }
        }
    }
}
