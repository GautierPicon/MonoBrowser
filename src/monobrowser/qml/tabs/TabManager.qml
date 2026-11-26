pragma ComponentBehavior: Bound

import QtQuick
import QtWebEngine
import ".."

Item {
    id: manager

    property var host: null
    property var controller: null

    property int currentIndex: -1
    property var views: []
    property var address: ""
    property bool adblockCosmetic: false
    property var closedTabs: []
    property int closedCount: 0

    width: 0
    height: 0

    readonly property var currentView:
        currentIndex >= 0 && currentIndex < views.length ? views[currentIndex] : null

    readonly property var bridge: host ? host.bridge : null
    readonly property var windowRef: host
    readonly property Item contentArea: host ? host.contentArea : null
    readonly property var navBar: windowRef ? windowRef.navBar : null
    readonly property var loadingBar: windowRef ? windowRef.loadingBar : null
    readonly property var linkBar: windowRef ? windowRef.linkBar : null
    readonly property var findBar: windowRef ? windowRef.findBar : null
    readonly property var zoomHud: windowRef ? windowRef.zoomHud : null

    ListModel { id: tabs }

    Component {
        id: tabViewComponent

        WebTab {
            anchors.fill: parent
        }
    }

    readonly property ListModel tabsModel: tabs

    function viewAt(index) {
        return index >= 0 && index < views.length ? views[index] : null
    }

    function setRole(index, role, value) {
        if (index < 0 || index >= tabs.count)
            return
        if (typeof value !== "string" && typeof value !== "boolean")
            return
        if (tabs.get(index)[role] === value)
            return
        tabs.setProperty(index, role, value)
    }

    function reindexViews() {
        for (let i = 0; i < views.length; ++i) {
            if (views[i])
                views[i].tabIndex = i
        }
    }

    function restoreSessionOrNewTab() {
        sessionController.restoreSessionOrNewTab()
    }

    function saveSessionState() {
        sessionController.saveSessionState()
    }

    function addTab(url, atIndex, seed) {
        var view = createView()
        if (!view)
            return -1
        var target = url !== undefined && url !== null ? url : ""
        var index = atIndex === undefined ? tabs.count : Math.max(0, Math.min(atIndex, tabs.count))
        var title = seed !== undefined && seed !== null && seed.title !== "" ? String(seed.title) : "New Tab"
        var icon = seed !== undefined && seed !== null && seed.favicon !== undefined && seed.favicon !== null
                   ? String(seed.favicon) : ""
        views.splice(index, 0, view)
        tabs.insert(index, {
            title: title,
            url: target,
            favicon: icon,
            loading: false,
            audible: false,
            muted: false
        })
        reindexViews()
        if (target !== "")
            view.url = target
        else
            view.loadHtml(bridge.newtabHtml(), "about:newtab")
        setCurrentIndex(index)
        if (target === "" && index > 0)
            focusAddress()
        return index
    }

    function createView() {
        var view = tabViewComponent.createObject(contentArea,
                                                  { tabIndex: views.length,
                                                    bridge: manager.bridge,
                                                    cosmeticCss: manager.adblockCosmetic })
        if (view === null) {
            console.warn("WebTab.qml: failed to create tab view")
            return null
        }
        connector.connectView(view)
        return view
    }

    function updateLifecycle(view) {
        if (!view)
            return
        var active = views.indexOf(view) === currentIndex
                  || (controller && view === controller.pipView)
                  || view.recentlyAudible
                  || view.loading
        view.lifecycleState = active ? WebEngineView.LifecycleState.Active
                                     : WebEngineView.LifecycleState.Frozen
    }

    function updateProgress(view) {
        if (view !== currentView)
            return
        loadingBar.visible = view.loading
        loadingBar.value = view.loadProgress / 100.0
    }

    function updateChrome(view) {
        navBar.certificateError = view.certificateError
        navBar.refreshHistory(view.canGoBack, view.canGoForward)
        navBar.loading = view.loading
        loadingBar.visible = view.loading
        loadingBar.value = view.loadProgress / 100.0
    }

    function syncView(view) {
        if (controller) {
            controller.pipProbeMisses = 0
            controller.pipProbeCooldown = 0
        }
        var index = view.tabIndex
        if (index < 0)
            return

        var text = String(view.url)
        var route = bridge.internalRoute(text)
        var action = route[0]
        var param = route[1]

        if (action === "retry") {
            if (param !== "")
                view.url = param
            return
        }
        if (action === "set-search") {
            bridge.searchEngine = param
            loadAbout(view, "settings")
            return
        }
        if (action === "set-restore") {
            bridge.restoreSession = !bridge.restoreSession
            loadAbout(view, "settings")
            return
        }
        if (action === "set-theme") {
            bridge.themeMode = param
            loadAbout(view, "settings")
            return
        }
        if (action === "set-adblock") {
            bridge.adblockEnabled = !bridge.adblockEnabled
            syncAdblockCosmetic()
            loadAbout(view, "settings")
            return
        }
        if (action === "set-adblock-cosmetic") {
            bridge.adblockCosmetic = !bridge.adblockCosmetic
            syncAdblockCosmetic()
            loadAbout(view, "settings")
            return
        }
        if (action === "set-antitrack") {
            bridge.antitrackEnabled = !bridge.antitrackEnabled
            loadAbout(view, "settings")
            return
        }
        if (action === "clear-history") {
            bridge.clearHistory()
            loadAbout(view, "history")
            return
        }
        if (action === "remove-history") {
            if (param !== "")
                bridge.removeHistoryEntry(param)
            loadAbout(view, "history")
            return
        }
        if (action === "search") {
            if (param !== "")
                view.url = bridge.resolveAddress(param)
            else
                loadAbout(view, "newtab")
            return
        }

        if (bridge.isExternalUrl(text))
            return

        setRole(index, "title", view.title !== "" ? view.title : "New Tab")
        setRole(index, "url", text)
        setRole(index, "loading", view.loading)
        faviconPoller.refreshIcon(view)
        bridge.recordHistory(text, view.title !== "" ? String(view.title) : "",
                             view.historyIconHref || "")

        if (view !== currentView)
            return

        address = text === "about:newtab" ? "" : text
        updateChrome(view)
    }

    function updateVisibility() {
        for (let i = 0; i < views.length; ++i) {
            const view = views[i]
            if (!view)
                continue
            view.visible = i === currentIndex || (controller && view === controller.pipView)
            updateLifecycle(view)
        }
    }

    function setCurrentIndex(index) {
        if (index < 0 || index >= tabs.count)
            return
        if (controller) {
            controller.pipProbeMisses = 0
            controller.pipProbeCooldown = 0
        }
        linkBar.target = ""
        if (findBar.visible)
            findBar.close()
        currentIndex = index
        updateVisibility()
        var current = currentView
        if (current) {
            const url = current.url.toString()
            address = url === "about:newtab" ? "" : url
            updateChrome(current)
            current.forceActiveFocus()
            faviconPoller.refreshIcon(current)
        }
        if (controller)
            controller.updatePipAvailability()
    }

    function openAbout(kind) {
        var index = addTab()
        var view = viewAt(index)
        if (!view)
            return
        loadAbout(view, kind)
    }

    function loadAbout(view, kind) {
        if (kind === "settings")
            view.loadHtml(bridge.settingsHtml(), "about:settings")
        else if (kind === "version")
            view.loadHtml(bridge.versionHtml(), "about:version")
        else if (kind === "history")
            view.loadHtml(bridge.historyHtml(), "about:history")
        else
            view.loadHtml(bridge.newtabHtml(), "about:newtab")
    }

    function closeTab(index) {
        if (tabs.count <= 1 || index < 0 || index >= tabs.count)
            return

        var previous = currentIndex
        var view = views[index]
        if (view !== null && controller && view === controller.pipView)
            controller.exitPip()
        var closedUrl = view !== null ? String(view.url) : ""
        if (view !== null && closedUrl !== "" && closedUrl.indexOf("about:") !== 0) {
            closedTabs.push({
                title: view.title !== "" ? view.title : closedUrl,
                url: closedUrl,
                index: index,
                favicon: view.icon !== undefined && view.icon !== null ? String(view.icon) : ""
            })
            if (closedTabs.length > 20)
                closedTabs.shift()
            closedCount = closedTabs.length
        }
        tabs.remove(index)
        views.splice(index, 1)
        if (view)
            view.destroy()
        reindexViews()

        if (index < previous)
            setCurrentIndex(previous - 1)
        else if (index === previous)
            setCurrentIndex(Math.min(index, tabs.count - 1))
    }

    function focusAddress() {
        navBar.focusAddress()
    }

    function moveTab(from, to) {
        if (from === to || from < 0 || to < 0 || from >= tabs.count || to >= tabs.count)
            return
        tabs.move(from, to, 1)
        views.splice(to, 0, views.splice(from, 1)[0])
        reindexViews()
        var c = currentIndex
        if (from === c)
            c = to
        else if (from < c && to >= c)
            c = c - 1
        else if (from > c && to <= c)
            c = c + 1
        if (c !== currentIndex)
            setCurrentIndex(c)
    }

    function reopenClosedTab() {
        if (closedTabs.length === 0)
            return
        var item = closedTabs.pop()
        closedCount = closedTabs.length
        addTab(item.url, item.index, item)
    }

    function zoomChange(step) {
        var view = currentView
        if (!view)
            return
        var factor = Math.round((view.zoomFactor + step) * 10) / 10
        factor = Math.min(3.0, Math.max(0.3, factor))
        if (view.zoomFactor !== factor)
            view.zoomFactor = factor
        zoomHud.show(Math.round(factor * 100))
    }

    function zoomReset() {
        var view = currentView
        if (view)
            view.zoomFactor = 1.0
        zoomHud.show(100)
    }

    function cycleTab(delta) {
        if (tabs.count <= 1)
            return
        setCurrentIndex((currentIndex + delta + tabs.count) % tabs.count)
    }

    function toggleTabMute(index) {
        if (index < 0 || index >= views.length)
            return
        var view = views[index]
        if (view)
            view.audioMuted = !view.audioMuted
    }

    function navigate(text) {
        var target = currentView
        if (!target || text === "")
            return
        if (text === "about:version")
            loadAbout(target, "version")
        else if (text === "about:newtab")
            loadAbout(target, "newtab")
        else if (text === "about:settings")
            loadAbout(target, "settings")
        else if (text === "about:history")
            loadAbout(target, "history")
        else
            target.url = bridge.resolveAddress(text)
    }

    function reloadCurrent() {
        var view = currentView
        if (!view)
            return
        var url = String(view.url)
        if (url === "about:settings" || url === "about:version"
                || url === "about:history" || url === "about:newtab")
            loadAbout(view, url.substring(6))
        else
            view.reload()
    }

    function reloadAboutPages() {
        for (let i = 0; i < views.length; ++i) {
            let view = views[i]
            if (!view)
                continue
            let u = String(view.url)
            if (u === "about:settings")
                loadAbout(view, "settings")
            else if (u === "about:version")
                loadAbout(view, "version")
            else if (u === "about:history")
                loadAbout(view, "history")
            else if (u === "about:newtab")
                loadAbout(view, "newtab")
        }
    }

    function syncAdblockCosmetic() {
        var on = bridge ? (bridge.adblockEnabled && bridge.adblockCosmetic) : false
        adblockCosmetic = on
        for (let i = 0; i < views.length; ++i) {
            if (views[i])
                views[i].cosmeticCss = on
        }
    }

    FaviconPoller {
        id: faviconPoller
        host: manager
    }

    SessionController {
        id: sessionController
        host: manager
    }

    TabConnector {
        id: connector
        host: manager
        poller: faviconPoller
    }
}
