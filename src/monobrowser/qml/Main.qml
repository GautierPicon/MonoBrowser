import QtQuick
import QtQuick.Controls
import QtWebEngine
import "chrome"

Window {
    id: window
    width: 1200
    height: 800
    visible: true
    minimumWidth: 480
    minimumHeight: 320
    color: Theme.tabstripBg

    flags: Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
         | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
         | Qt.ExpandedClientAreaHint | Qt.NoTitleBarBackgroundHint

    ListModel { id: tabs }

    Component {
        id: tabViewComponent

        WebTab {
            anchors.fill: parent
        }
    }

    property int currentIndex: -1
    property var views: []
    property var address: ""
    property var bridge: null
    property var pipView: null
    property bool canPip: false
    property var closedTabs: []
    property int closedCount: 0

    readonly property var currentView:
        currentIndex >= 0 && currentIndex < views.length ? views[currentIndex] : null

    function viewAt(index) {
        return index >= 0 && index < views.length ? views[index] : null
    }

    function togglePip() {
        if (pipView !== null) {
            exitPip()
            return
        }
        var view = currentView
        if (!view)
            return
        view.probeVideo(function (rect) {
            if (rect === null || rect === undefined || view !== currentView)
                return
            enterPip(view, rect)
        })
    }

    function enterPip(view, rect) {
        if (view !== currentView)
            return
        if (pipRectVisible(rect) || !rect[5]) {
            attachPip(view, rect)
            return
        }
        view.scrollVideoIntoView(rect[5], function () {
            view.probeVideo(function (fresh) {
                attachPip(view, fresh === null || fresh === undefined ? rect : fresh)
            })
        })
    }

    function pipRectVisible(rect) {
        return rect[0] >= -2 && rect[1] >= -2
            && rect[0] + rect[2] <= contentArea.width + 2
            && rect[1] + rect[3] <= contentArea.height + 2
    }

    function attachPip(view, rect) {
        if (pipView === view || view !== currentView)
            return
        if (pipView !== null)
            exitPip()
        pipView = view
        pipWindow.open(view, contentArea, {
            x: rect[0],
            y: rect[1],
            width: rect[2],
            height: rect[3]
        })
        updateVisibility()
        updateLifecycle(view)
        linkBar.target = ""
    }

    function exitPip() {
        if (pipView === null)
            return
        var view = pipView
        pipView = null
        pipWindow.release()
        updateVisibility()
        updateLifecycle(view)
        if (view === currentView)
            view.forceActiveFocus()
        updatePipAvailability()
    }

    function applyPipRect(view, rect) {
        if (view !== pipView)
            return
        pipWindow.setVideoRect({
            x: rect[0],
            y: rect[1],
            width: rect[2],
            height: rect[3]
        })
    }

    function refreshPip() {
        var view = pipView
        if (view === null || !pipWindow.visible)
            return
        view.probeVideo(function (rect) {
            if (view !== pipView)
                return
            if (rect !== null && rect !== undefined && rect[4] !== 1) {
                applyPipRect(view, rect)
                return
            }
            view.probeVideo(function (paused) {
                if (paused === null || paused === undefined || paused[4] === 1)
                    exitPip()
                else
                    applyPipRect(view, paused)
            }, false)
        })
    }

    function updatePipAvailability() {
        var view = currentView
        if (pipView !== null || !view || !window.active) {
            canPip = false
            return
        }
        view.probeVideo(function (rect) {
            if (view === currentView && pipView === null)
                canPip = rect !== null && rect !== undefined
        })
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

    function addTab(url, atIndex) {
        var view = createView()
        if (!view)
            return -1
        var target = url !== undefined && url !== null ? url : ""
        var index = atIndex === undefined ? tabs.count : Math.max(0, Math.min(atIndex, tabs.count))
        views.splice(index, 0, view)
        tabs.insert(index, {
            title: "New Tab",
            url: target,
            favicon: "",
            loading: false
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
                                                 { tabIndex: views.length })
        if (view === null) {
            console.warn("WebTab.qml: failed to create tab view")
            return null
        }
        connectView(view)
        return view
    }

    function connectView(view) {
        view.pageChanged.connect(function () { syncView(view) })
        view.progressChanged.connect(function () { updateProgress(view) })
        view.popupRequested.connect(function () {
            var index = addTab()
            if (index >= 0)
                view.openPending(views[index])
        })
        view.recentlyAudibleChanged.connect(function () { updateLifecycle(view) })
        view.loadingChanged.connect(function (info) {
            if (info.status !== WebEngineView.LoadFailedStatus)
                return
            var url = String(info.url)
            if (url === "" || url.indexOf("about:") === 0
                    || url.indexOf("https://monobrowser.internal") === 0)
                return
            if (info.errorCode === -3)
                return
            view.loadHtml(bridge.errorHtml(url, String(info.errorString)), url)
        })
        view.certificateErrorChanged.connect(function () {
            if (view === currentView)
                navBar.certificateError = view.certificateError
        })
        view.hoveredLink.connect(function (target) {
            if (view === currentView)
                linkBar.target = target
        })
        view.urlChanged.connect(function () {
            if (view === currentView)
                linkBar.target = ""
        })
    }

    function updateLifecycle(view) {
        if (!view)
            return
        var active = views.indexOf(view) === currentIndex
                  || view === pipView
                  || view.recentlyAudible
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
        var index = view.tabIndex
        if (index < 0)
            return

        var text = String(view.url)
        var action = bridge.internalAction(text)

        if (action === "retry") {
            var retryTarget = bridge.internalParam(text)
            if (retryTarget !== "")
                view.url = retryTarget
            return
        }
        if (action === "set-search") {
            bridge.searchEngine = bridge.internalParam(text)
            loadAbout(view, "settings")
            return
        }
        if (action === "search") {
            const query = bridge.internalParam(text)
            if (query !== "")
                view.url = bridge.resolveAddress(query)
            else
                loadAbout(view, "newtab")
            return
        }

        setRole(index, "title", view.title !== "" ? view.title : "New Tab")
        setRole(index, "url", text)
        setRole(index, "loading", view.loading)
        var icon = view.icon
        setRole(index, "favicon",
                icon !== undefined && icon !== null ? String(icon) : "")

        if (view !== currentView)
            return

        address = text === "about:newtab" ? "" : text
        updateChrome(view)
    }

    function toggleZoom() {
        if (visibility === Window.Maximized || visibility === Window.FullScreen)
            showNormal()
        else
            showMaximized()
    }

    function updateVisibility() {
        for (let i = 0; i < views.length; ++i) {
            const view = views[i]
            if (!view)
                continue
            view.visible = i === currentIndex || view === pipView
            updateLifecycle(view)
        }
    }

    function setCurrentIndex(index) {
        if (index < 0 || index >= tabs.count)
            return
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
        }
        updatePipAvailability()
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
        else
            view.loadHtml(bridge.newtabHtml(), "about:newtab")
    }

    function closeTab(index) {
        if (tabs.count <= 1 || index < 0 || index >= tabs.count)
            return

        var previous = currentIndex
        var view = views[index]
        if (view !== null && view === pipView)
            exitPip()
        var closedUrl = view !== null ? String(view.url) : ""
        if (view !== null && closedUrl !== "" && closedUrl.indexOf("about:") !== 0) {
            closedTabs.push({
                title: view.title !== "" ? view.title : closedUrl,
                url: closedUrl,
                index: index
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
        var view = views[from]
        var items = []
        for (let i = 0; i < tabs.count; ++i) {
            var entry = tabs.get(i)
            items.push({ title: entry.title, url: entry.url,
                         favicon: entry.favicon, loading: entry.loading })
        }
        var moved = items.splice(from, 1)[0]
        items.splice(to, 0, moved)
        tabs.clear()
        for (let j = 0; j < items.length; ++j)
            tabs.append(items[j])
        views.splice(from, 1)
        views.splice(to, 0, view)
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
        addTab(item.url, item.index)
    }

    function zoomChange(step) {
        var view = currentView
        if (!view)
            return
        var factor = Math.round((view.zoomFactor + step) * 10) / 10
        factor = Math.min(3.0, Math.max(0.3, factor))
        if (view.zoomFactor !== factor)
            view.zoomFactor = factor
        chrome.zoomHud.show(Math.round(factor * 100))
    }

    function zoomReset() {
        var view = currentView
        if (view)
            view.zoomFactor = 1.0
        chrome.zoomHud.show(100)
    }

    function cycleTab(delta) {
        if (tabs.count <= 1)
            return
        setCurrentIndex((currentIndex + delta + tabs.count) % tabs.count)
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
        else
            target.url = bridge.resolveAddress(text)
    }

    BrowserChrome {
        id: chrome
        anchors.fill: parent
        tabModel: tabs
        currentIndex: window.currentIndex
        address: window.address
        bridge: window.bridge
        windowRef: window
        canPip: window.canPip
        pipActive: window.pipView !== null
        pipDetached: window.pipView !== null && window.pipView === window.currentView
        pipTitle: window.pipView !== null ? window.pipView.title : ""
        onTabClicked: function (index) { window.setCurrentIndex(index) }
        onTabClosed: function (index) { window.closeTab(index) }
        onTabMoved: function (from, to) { window.moveTab(from, to) }
        onNewTabRequested: window.addTab()
        onBackgroundPressed: window.startSystemMove()
        onBackgroundDoubleClicked: window.toggleZoom()
        onAddressSubmitted: function (text) { window.navigate(text) }
        onBackRequested: if (window.currentView) window.currentView.goBack()
        onForwardRequested: if (window.currentView) window.currentView.goForward()
        onReloadRequested: if (window.currentView) window.currentView.reload()
        onStopRequested: if (window.currentView) window.currentView.stop()
        onPipRequested: window.togglePip()
    }

    readonly property var navBar: chrome.navBar
    readonly property var loadingBar: chrome.loadingBar
    readonly property var linkBar: chrome.linkBar
    readonly property var findBar: chrome.findBar
    readonly property Item contentArea: chrome.contentArea

    Shortcut { sequences: ["Ctrl+T"]; onActivated: window.addTab() }
    Shortcut { sequences: ["Ctrl+W"]; onActivated: window.closeTab(window.currentIndex) }
    Shortcut { sequences: ["Ctrl+L"]; onActivated: window.focusAddress() }
    Shortcut { sequences: ["Ctrl+,"]; onActivated: window.openAbout("settings") }
    Shortcut { sequences: ["Ctrl+R"]; onActivated: if (window.currentView) window.currentView.reload() }
    Shortcut { sequences: ["Ctrl+Shift+P"]; onActivated: window.togglePip() }
    Shortcut { sequences: ["Escape"]; onActivated: if (window.findBar.visible) window.findBar.close(); else if (window.currentView) window.currentView.stop() }
    Shortcut { sequences: ["Ctrl+F"]; onActivated: window.findBar.toggle() }
    Shortcut { sequences: ["Ctrl+Shift+BracketLeft"]; onActivated: window.cycleTab(-1) }
    Shortcut { sequences: ["Ctrl+Shift+BracketRight"]; onActivated: window.cycleTab(1) }
    Shortcut { sequences: ["Ctrl+Shift+T"]; onActivated: window.reopenClosedTab() }
    Shortcut { sequences: ["Ctrl+=", "Ctrl+Plus"]; onActivated: window.zoomChange(0.1) }
    Shortcut { sequences: ["Ctrl+-", "Ctrl+Minus"]; onActivated: window.zoomChange(-0.1) }
    Shortcut { sequences: ["Ctrl+0"]; onActivated: window.zoomReset() }

    PipWindow {
        id: pipWindow
        bridge: window.bridge
        onExitRequested: window.exitPip()
    }

    Timer {
        interval: 1000
        repeat: true
        running: pipWindow.visible
        onTriggered: window.refreshPip()
    }

    Timer {
        interval: 1200
        repeat: true
        running: window.active && window.pipView === null
        onTriggered: window.updatePipAvailability()
    }

    onActiveChanged: window.updatePipAvailability()
    onClosing: window.exitPip()

    Component.onCompleted: addTab()
}
