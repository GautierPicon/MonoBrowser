import QtQuick

Item {
    id: poller

    property var host: null

    width: 0
    height: 0

    readonly property var bridge: host ? host.bridge : null

    property var iconPollQueue: []
    property int iconPollTicks: 0

    Timer {
        id: iconPollTimer
        interval: 400
        repeat: true
        running: poller.iconPollQueue.length > 0
        onTriggered: poller.pollIconQueue()
    }

    function armIconPoll(view) {
        if (!view)
            return
        if (iconPollQueue.indexOf(view) === -1)
            iconPollQueue = iconPollQueue.concat([view])
        iconPollTicks = 0
    }

    function pollIconQueue() {
        iconPollTicks = iconPollTicks + 1
        var remaining = []
        for (let i = 0; i < iconPollQueue.length; ++i) {
            let v = iconPollQueue[i]
            let raw = ""
            try {
                if (v && v.icon !== undefined && v.icon !== null)
                    raw = String(v.icon)
            } catch (e) {
                v = null
            }
            if (!v)
                continue
            if (raw !== "")
                refreshIcon(v)
            else
                remaining.push(v)
        }
        iconPollQueue = remaining
        if (remaining.length === 0 || iconPollTicks > 20)
            iconPollQueue = []
    }

    function refreshIcon(view, explicitSrc) {
        if (!view)
            return
        var text = String(view.url)
        var raw = explicitSrc !== undefined
                  ? String(explicitSrc)
                  : (view.icon !== undefined && view.icon !== null ? String(view.icon) : "")
        var src = bridge ? bridge.faviconSource(raw) : raw
        if (src === "" && text.indexOf("about:") === 0)
            src = bridge.iconUrl("svg/mono.svg", "#86868b")
        host.setRole(view.tabIndex, "favicon", src)
    }
}
