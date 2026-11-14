pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine
import ".."

Item {
    id: root

    property var windowRef: null
    property bool caseSensitive: false
    property int totalMatches: 0
    property int activeMatch: 0

    readonly property var currentView: root.windowRef ? root.windowRef.currentView : null

    visible: false
    z: 60
    implicitWidth: 336
    implicitHeight: 36

    function flags(backward) {
        var f = root.caseSensitive ? WebEngineView.FindCaseSensitively : 0
        if (backward)
            f |= WebEngineView.FindBackward
        return f
    }

    function applyFind(backward) {
        var view = root.currentView
        var query = field.text
        if (!view)
            return
        if (query === "") {
            root.totalMatches = 0
            root.activeMatch = 0
            view.findText("")
            return
        }
        view.findText(query, root.flags(backward === true))
    }

    function open() {
        if (!root.currentView)
            return
        root.visible = true
        root.applyFind(false)
        field.forceActiveFocus()
        field.selectAll()
    }

    function close() {
        if (!root.visible)
            return
        root.visible = false
        var view = root.currentView
        if (view) {
            view.findText("")
            view.forceActiveFocus()
        }
    }

    function toggle() {
        if (root.visible)
            root.close()
        else
            root.open()
    }

    readonly property string counterText: field.text === "" ? ""
        : (root.totalMatches === 0 ? "0/0" : root.activeMatch + "/" + root.totalMatches)

    Connections {
        target: root.currentView
        ignoreUnknownSignals: true

        function onFindTextFinished(result) {
            root.totalMatches = result.numberOfMatches
            root.activeMatch = result.activeMatch
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 8
        color: Theme.toolbarBg
        border.width: 1
        border.color: Theme.border
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 2

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 6
            color: Theme.urlbarBg
            border.width: 1
            border.color: field.activeFocus ? Theme.urlbarFocus : Theme.urlbarBorder

            Behavior on border.color {
                ColorAnimation { duration: 120 }
            }

            TextField {
                id: field
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 4
                verticalAlignment: TextInput.AlignVCenter
                background: null
                color: Theme.textActive
                placeholderText: "Find in page"
                placeholderTextColor: Theme.textInactive
                selectionColor: Theme.urlbarFocus
                selectedTextColor: Theme.textActive
                font.pixelSize: 13
                selectByMouse: true

                onTextEdited: root.applyFind(false)

                Keys.onReturnPressed: function (event) {
                    event.accepted = true
                    var backward = (event.modifiers & Qt.ShiftModifier) !== 0
                    root.applyFind(backward)
                }

                Keys.onEscapePressed: root.close()
            }
        }

        Text {
            Layout.preferredWidth: 38
            text: root.counterText
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 11
            color: Theme.textInactive
        }

        Rectangle {
            id: caseToggle
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            radius: 5
            color: root.caseSensitive ? Theme.urlbarFocus : (caseHover.hovered ? Theme.newtabHover : "transparent")

            Text {
                anchors.centerIn: parent
                text: "Aa"
                font.pixelSize: 12
                font.weight: Font.Medium
                color: root.caseSensitive ? "#FFFFFF" : Theme.textInactive
            }

            HoverHandler { id: caseHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: { root.caseSensitive = !root.caseSensitive; root.applyFind(false) } }
        }

        Rectangle {
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            radius: 5
            color: prevHover.hovered ? Theme.newtabHover : "transparent"

            Text {
                anchors.centerIn: parent
                text: "↑"
                font.pixelSize: 14
                color: Theme.textActive
            }

            HoverHandler { id: prevHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: root.applyFind(true) }
        }

        Rectangle {
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            radius: 5
            color: nextHover.hovered ? Theme.newtabHover : "transparent"

            Text {
                anchors.centerIn: parent
                text: "↓"
                font.pixelSize: 14
                color: Theme.textActive
            }

            HoverHandler { id: nextHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: root.applyFind(false) }
        }

        Rectangle {
            Layout.preferredWidth: 24
            Layout.preferredHeight: 24
            radius: 5
            color: closeHover.hovered ? Theme.newtabHover : "transparent"

            Text {
                anchors.centerIn: parent
                text: "✕"
                font.pixelSize: 12
                color: Theme.textInactive
            }

            HoverHandler { id: closeHover; cursorShape: Qt.PointingHandCursor }
            TapHandler { onTapped: root.close() }
        }
    }
}
