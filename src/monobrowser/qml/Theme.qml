pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: Qt.styleHints.colorScheme === Qt.Dark

    readonly property color tabstripBg: dark ? "#282A2D" : "#F1F3F4"
    readonly property color tabActiveBg: dark ? "#35373B" : "#FFFFFF"
    readonly property color tabHoverBg: dark ? "#333639" : "#E7E9ED"
    readonly property color textActive: dark ? "#E8EAED" : "#202124"
    readonly property color textInactive: dark ? "#9AA0A6" : "#5F6368"
    readonly property color border: dark ? "#4A4D51" : "#DADCE0"
    readonly property color closeHoverBg: dark ? "#4A4D51" : "#DADCE0"
    readonly property color closeGlyph: dark ? "#9AA0A6" : "#5F6368"
    readonly property color toolbarBg: dark ? "#35373B" : "#FFFFFF"
    readonly property color urlbarBg: dark ? "#202124" : "#FFFFFF"
    readonly property color urlbarBorder: dark ? "#4A4D51" : "#DADCE0"
    readonly property color urlbarFocus: "#5B8DEF"
    readonly property color iconNormal: dark ? "#E8EAED" : "#202124"
    readonly property color iconDisabled: dark ? "#5F6368" : "#9AA0A6"
    readonly property color newtabHover: dark ? "#45484D" : "#C7CBD1"
    readonly property color progress: "#5B8DEF"

    readonly property color trafficClose: "#FF5F57"
    readonly property color trafficMinimize: "#FEBC2E"
    readonly property color trafficZoom: "#28C840"
    readonly property color trafficInactive: dark ? "#4D4D4D" : "#D8D8D8"
}
