import QtQuick
import QtWebEngine
import "../scripts/pageScripts.js" as PageScripts

QtObject {
    id: connector

    property var host: null
    property var poller: null

    function connectView(view) {
        view.pageChanged.connect(function () { host.syncView(view) })
        view.progressChanged.connect(function () { host.updateProgress(view) })
        view.popupRequested.connect(function () {
            var index = host.addTab()
            if (index >= 0)
                view.openPending(host.views[index])
        })
        view.recentlyAudibleChanged.connect(function () {
            host.setRole(view.tabIndex, "audible", view.recentlyAudible)
            host.updateLifecycle(view)
        })
        view.audioMutedChanged.connect(function (muted) { host.setRole(view.tabIndex, "muted", muted) })
        view.loadingChanged.connect(function (info) {
            host.updateLifecycle(view)
            if (info.status === WebEngineView.LoadSucceededStatus) {
                poller.armIconPoll(view)
                view.runJavaScript(PageScripts.iconLinkScript(), function (href) {
                    if (href === undefined || href === null || String(href) === "")
                        return
                    poller.refreshIcon(view, String(href))
                })
            }
            if (info.status !== WebEngineView.LoadFailedStatus)
                return
            var url = String(info.url)
            if (url === "" || url.indexOf("about:") === 0
                    || url.indexOf("https://monobrowser.internal") === 0)
                return
            if (info.errorCode === -3)
                return
            view.loadHtml(host.bridge.errorHtml(url, String(info.errorString)), url)
        })
        view.certificateErrorChanged.connect(function () {
            if (view === host.currentView)
                host.navBar.certificateError = view.certificateError
        })
        view.hoveredLink.connect(function (target) {
            if (view === host.currentView)
                host.linkBar.target = target
        })
        view.urlChanged.connect(function () {
            if (view === host.currentView)
                host.linkBar.target = ""
        })
    }
}
