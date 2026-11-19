pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtWebEngine
import ".."

Item {
    id: root

    property var bridge: null
    property var activeDownloads: ({})

    readonly property int maxVisible: 3

    component ToastButton: Rectangle {
        id: button

        property string iconName: ""
        property string tip: ""

        signal activated()

        implicitWidth: 28
        implicitHeight: 28
        radius: 6
        color: hover.hovered ? Theme.newtabHover : "transparent"

        IconImage {
            anchors.centerIn: parent
            bridge: root.bridge
            iconName: button.iconName
            color: Theme.menuText
            size: 15
        }

        HoverHandler {
            id: hover
            cursorShape: Qt.PointingHandCursor
        }

        TapHandler {
            onTapped: button.activated()
        }

        ToolTip.visible: hover.hovered && button.tip !== ""
        ToolTip.delay: 600
        ToolTip.text: button.tip
    }

    component DownloadTracker: Connections {
        property var download: null
        target: download

        function onReceivedBytesChanged() {
            root.patch(download.id, {
                received: download.receivedBytes,
                total: download.totalBytes
            })
        }

        function onTotalBytesChanged() {
            root.patch(download.id, {
                received: download.receivedBytes,
                total: download.totalBytes
            })
        }

        function onStateChanged(state) {
            const id = download.id
            if (state === WebEngineDownloadRequest.DownloadCompleted) {
                const total = download.totalBytes
                root.patch(id, {
                    state: "done",
                    received: total > 0 ? total : download.receivedBytes
                })
                root.removeTracker(id)
            } else if (state === WebEngineDownloadRequest.DownloadInterrupted) {
                root.patch(id, {
                    state: "failed",
                    error: download.interruptReasonString || "Download interrupted"
                })
                root.removeTracker(id)
            } else if (state === WebEngineDownloadRequest.DownloadCancelled) {
                root.dismiss(id)
                root.removeTracker(id)
            }
        }
    }

    Connections {
        target: WebEngine.defaultProfile

        function onDownloadRequested(download) {
            if (!root.bridge) {
                download.cancel()
                return
            }
            const dest = root.bridge.downloadDestination(
                download.suggestedFileName, String(download.url))
            download.downloadDirectory = dest[0]
            download.downloadFileName = dest[1]
            downloads.insert(0, {
                downloadId: download.id,
                name: dest[1],
                path: dest[0] + "/" + dest[1],
                received: 0,
                total: download.totalBytes,
                state: "running",
                error: ""
            })
            while (downloads.count > root.maxVisible)
                downloads.remove(downloads.count - 1)
            const tracker = trackerComponent.createObject(root, { download: download })
            if (tracker) {
                const map = root.activeDownloads
                map[download.id] = tracker
                root.activeDownloads = map
            }
            download.accept()
        }
    }

    Component {
        id: trackerComponent
        DownloadTracker {}
    }

    ListModel { id: downloads }

    function indexOfId(downloadId) {
        for (let i = 0; i < downloads.count; ++i)
            if (downloads.get(i).downloadId === downloadId)
                return i
        return -1
    }

    function dismiss(downloadId) {
        const i = indexOfId(downloadId)
        if (i >= 0)
            downloads.remove(i)
    }

    function patch(downloadId, fields) {
        const i = indexOfId(downloadId)
        if (i < 0)
            return
        for (const key in fields)
            downloads.setProperty(i, key, fields[key])
    }

    function cancel(downloadId) {
        const tracker = root.activeDownloads[downloadId]
        if (tracker && tracker.download)
            tracker.download.cancel()
    }

    function removeTracker(downloadId) {
        const map = root.activeDownloads
        const tracker = map[downloadId]
        if (tracker) {
            delete map[downloadId]
            root.activeDownloads = map
            tracker.destroy()
        }
    }

    function formatBytes(bytes) {
        if (bytes < 1024)
            return Math.round(bytes) + " B"
        const units = ["KB", "MB", "GB"]
        let value = bytes / 1024
        let unit = 0
        while (value >= 1024 && unit < units.length - 1) {
            value /= 1024
            unit += 1
        }
        return value.toFixed(value >= 100 ? 0 : 1) + " " + units[unit]
    }

    implicitWidth: 320
    implicitHeight: column.implicitHeight
    width: implicitWidth
    height: implicitHeight

    Column {
        id: column
        width: parent.width
        spacing: 8

        Repeater {
            model: downloads

            delegate: Rectangle {
                id: toast

                required property int downloadId
                required property string name
                required property string path
                required property double received
                required property double total
                required property string state
                required property string error

                width: column.width
                height: 64
                radius: 10
                color: Theme.menuBg
                border.width: 1
                border.color: Theme.menuBorder

                Timer {
                    interval: 6000
                    running: toast.state === "done"
                    onTriggered: root.dismiss(toast.downloadId)
                }

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 8
                    anchors.topMargin: 8
                    anchors.bottomMargin: 8
                    spacing: 10

                    IconImage {
                        anchors.verticalCenter: parent.verticalCenter
                        bridge: root.bridge
                        iconName: "svg/download.svg"
                        color: toast.state === "failed" ? "#FF453A" : Theme.menuText
                        size: 22
                    }

                    Column {
                        width: parent.width - 22 - 10 - buttons.width - 10
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 3

                        Text {
                            width: parent.width
                            text: toast.name
                            font.pixelSize: 12
                            font.weight: Font.Medium
                            color: Theme.menuText
                            elide: Text.ElideMiddle
                        }

                        Text {
                            width: parent.width
                            text: toast.state === "failed" ? toast.error
                                : toast.state === "done" ? "Download complete"
                                : toast.total > 0
                                    ? root.formatBytes(toast.received) + " of " + root.formatBytes(toast.total)
                                    : "Downloading… " + root.formatBytes(toast.received)
                            font.pixelSize: 11
                            color: toast.state === "failed" ? "#FF453A" : Theme.menuTextDim
                            elide: Text.ElideRight
                        }

                        Rectangle {
                            width: parent.width
                            height: 3
                            radius: 1.5
                            visible: toast.state === "running" && toast.total > 0
                            color: Theme.menuBorder

                            Rectangle {
                                width: parent.width * Math.min(1, Math.max(0, toast.received / toast.total))
                                height: parent.height
                                radius: parent.radius
                                color: Theme.progress
                            }
                        }
                    }

                    Row {
                        id: buttons
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2

                        ToastButton {
                            visible: toast.state === "done"
                            iconName: "svg/folder-open.svg"
                            tip: "Reveal in Finder"
                            onActivated: if (root.bridge) root.bridge.revealDownload(toast.path)
                        }

                        ToastButton {
                            visible: toast.state === "running"
                            iconName: "svg/tabs/close.svg"
                            tip: "Cancel download"
                            onActivated: root.cancel(toast.downloadId)
                        }

                        ToastButton {
                            visible: toast.state !== "running"
                            iconName: "svg/tabs/close.svg"
                            tip: "Dismiss"
                            onActivated: root.dismiss(toast.downloadId)
                        }
                    }
                }
            }
        }
    }
}
