import QtQuick
import "chrome"
import "scripts/pageScripts.js" as PageScripts

Item {
    id: root

    property var view: null
    property var bridge: null
    property alias swipeEnabled: swipeHandler.enabled

    property real accumX: 0
    property real accumY: 0
    property real pointerX: 0
    property real pointerY: 0
    property bool gestureSeen: false
    property bool gestureBack: true

    readonly property real threshold: 60
    readonly property real progress: Math.max(0, Math.min(1, Math.abs(accumX) / threshold))

    readonly property bool gestureValid:
        !view ? false : (gestureBack ? view.canGoBack : view.canGoForward)

    WheelHandler {
        id: swipeHandler
        orientation: Qt.Horizontal
        acceptedDevices: PointerDevice.TouchPad | PointerDevice.Mouse
        blocking: false
        onWheel: function (event) {
            root.pointerX = event.x
            root.pointerY = event.y
            var dx = event.pixelDelta.x !== 0 ? event.pixelDelta.x : event.angleDelta.x / 8
            var dy = event.pixelDelta.y !== 0 ? event.pixelDelta.y : event.angleDelta.y / 8
            if (!root.gestureSeen) {
                root.accumX = 0
                root.accumY = 0
                root.gestureSeen = true
            }
            root.accumX += dx
            root.accumY += dy
            if (Math.abs(root.accumX) > 1)
                root.gestureBack = root.accumX > 0
            root.updateBubble()
        }
        onActiveChanged: {
            if (!active)
                root.commitSwipe()
        }
    }

    function updateBubble() {
        bubble.direction = gestureBack
        bubble.frozen = progress
        bubble.shown = gestureSeen && gestureValid
    }

    function commitSwipe() {
        if (!gestureSeen)
            return
        var ax = accumX
        var ay = accumY
        var px = pointerX
        var py = pointerY
        gestureSeen = false
        accumX = 0
        accumY = 0
        updateBubble()
        if (Math.abs(ax) < threshold || Math.abs(ax) < Math.abs(ay) * 2)
            return
        var back = ax > 0
        var currentView = view
        if (!currentView)
            return
        if (back ? !currentView.canGoBack : !currentView.canGoForward)
            return
        currentView.runJavaScript(PageScripts.edgeProbeJs(back, px, py), function (result) {
            if (result !== "edge")
                return
            if (back) {
                if (currentView.canGoBack)
                    currentView.goBack()
            } else {
                if (currentView.canGoForward)
                    currentView.goForward()
            }
        })
    }


    Rectangle {
        id: bubble

        property bool direction: true
        property bool shown: false
        property real frozen: 0

        readonly property real margin: 12
        readonly property real diameter: 44
        readonly property real displayProgress: shown ? root.progress : frozen

        width: diameter
        height: diameter
        radius: diameter / 2
        z: 55
        anchors.verticalCenter: parent.verticalCenter
        x: direction
           ? -diameter + displayProgress * (diameter + margin)
           : parent.width - displayProgress * (diameter + margin)
        opacity: shown ? 1 : 0
        visible: opacity > 0
        color: Theme.menuBg
        border.width: 1
        border.color: Theme.menuBorder

        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }

        Item {
            anchors.fill: parent
            opacity: 0.35 + 0.65 * bubble.displayProgress

            IconImage {
                anchors.centerIn: parent
                bridge: root.bridge
                iconName: bubble.direction ? "svg/nav/back.svg" : "svg/nav/forward.svg"
                color: Theme.menuText
                size: 20
            }
        }
    }
}
