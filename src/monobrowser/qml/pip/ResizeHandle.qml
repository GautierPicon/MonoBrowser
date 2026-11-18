import QtQuick

MouseArea {
    id: handle

    property var windowRef: null
    property int edges: Qt.LeftEdge
    property int shape: Qt.SizeHorCursor

    hoverEnabled: true
    cursorShape: shape
    onPressed: if (windowRef) windowRef.startSystemResize(edges)
}
