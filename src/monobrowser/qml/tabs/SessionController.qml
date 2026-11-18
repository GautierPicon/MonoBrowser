import QtQuick

Item {
    id: session

    property var host: null

    width: 0
    height: 0

    readonly property var windowRef: host ? host.windowRef : null
    readonly property var bridge: host ? host.bridge : null

    function restoreSessionOrNewTab() {
        if (!windowRef)
            return
        var state = bridge ? bridge.loadSessionState() : null
        var urls = state && state.urls ? state.urls : null
        var ok = bridge && bridge.restoreSession && urls && urls.length > 0
        if (!ok) {
            host.addTab()
            return
        }
        var geo = state.geometry
        if (geo && geo.width >= 480 && geo.height >= 320) {
            windowRef.x = geo.x
            windowRef.y = geo.y
            windowRef.width = geo.width
            windowRef.height = geo.height
        }
        for (let i = 0; i < urls.length; ++i) {
            let u = String(urls[i])
            if (u === "about:settings" || u === "about:version") {
                let aboutIndex = host.addTab()
                let aboutView = host.viewAt(aboutIndex)
                if (aboutView)
                    host.loadAbout(aboutView, u === "about:version" ? "version" : "settings")
            } else if (u === "" || u.indexOf("about:") === 0
                       || u.indexOf("https://monobrowser.internal") === 0) {
                host.addTab()
            } else {
                host.addTab(u)
            }
        }
        var savedIndex = typeof state.current_index === "number" ? state.current_index : 0
        host.setCurrentIndex(Math.max(0, Math.min(savedIndex, host.tabsModel.count - 1)))
        if (geo && geo.maximized === true)
            windowRef.showMaximized()
    }

    function saveSessionState() {
        if (!bridge || !windowRef)
            return
        var urls = []
        for (let i = 0; i < host.views.length; ++i) {
            let view = host.views[i]
            let url = view ? String(view.url) : ""
            urls.push(url === "" ? "about:newtab" : url)
        }
        var big = windowRef.visibility === Window.Maximized || windowRef.visibility === Window.FullScreen
        bridge.saveSession(urls, Math.max(0, host.currentIndex), windowRef.x, windowRef.y, windowRef.width, windowRef.height, big)
    }
}
