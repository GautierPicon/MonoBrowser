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

    readonly property var currentView:
        currentIndex >= 0 && currentIndex < views.length ? views[currentIndex] : null

    function viewAt(index) {
        return index >= 0 && index < views.length ? views[index] : null
    }

    function setRole(index, role, value) {
        if (index < 0 || index >= tabs.count)
            return
        if (typeof value !== "string")
            return
        tabs.setProperty(index, role, value)
    }

    function addTab(url) {
        var view = createView()
        if (!view)
            return -1
        views.push(view)
        var target = url !== undefined && url !== null ? url : ""
        tabs.append({
            title: "New Tab",
            url: target,
            favicon: ""
        })
        var index = tabs.count - 1
        if (target !== "")
            view.url = target
        else
            view.loadHtml(bridge.newtabHtml(), "about:newtab")
        setCurrentIndex(index)
        if (index > 0)
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
        view.popupRequested.connect(function () {
            var index = addTab()
            if (index >= 0)
                view.openPending(views[index])
        })
        view.recentlyAudibleChanged.connect(function () { updateLifecycle(view) })
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
        var active = views.indexOf(view) === currentIndex || view.recentlyAudible
        view.lifecycleState = active ? WebEngineView.LifecycleState.Active
                                     : WebEngineView.LifecycleState.Frozen
    }

    function syncView(view) {
        var index = view.tabIndex
        if (index < 0)
            return

        var text = String(view.url)
        var action = bridge.internalAction(text)

        if (action === "set-search") {
            bridge.searchEngine = bridge.internalParam(text)
            view.loadHtml(bridge.settingsHtml(), "about:settings")
            return
        }
        if (action === "search") {
            const query = bridge.internalParam(text)
            if (query !== "")
                view.url = bridge.resolveAddress(query)
            else
                view.loadHtml(bridge.newtabHtml(), "about:newtab")
            return
        }

        setRole(index, "title", view.title !== "" ? view.title : "New Tab")
        setRole(index, "url", text)
        var icon = view.icon
        setRole(index, "favicon",
                icon !== undefined && icon !== null ? String(icon) : "")

        if (view !== currentView)
            return

        address = text === "about:newtab" ? "" : text
        navBar.certificateError = view.certificateError
        navBar.refreshHistory(view.canGoBack, view.canGoForward)
        navBar.loading = view.loading
        loadingBar.visible = view.loading
        loadingBar.value = view.loadProgress / 100.0
    }

    function toggleZoom() {
        if (visibility === Window.Maximized || visibility === Window.FullScreen)
            showNormal()
        else
            showMaximized()
    }

    function setCurrentIndex(index) {
        if (index < 0 || index >= tabs.count)
            return
        linkBar.target = ""
        currentIndex = index
        for (let i = 0; i < views.length; ++i) {
            const view = views[i]
            if (!view)
                continue
            view.visible = i === index
            updateLifecycle(view)
        }
        var current = currentView
        if (current) {
            const url = current.url.toString()
            address = url === "about:newtab" ? "" : url
            navBar.certificateError = current.certificateError
            navBar.refreshHistory(current.canGoBack, current.canGoForward)
            navBar.loading = current.loading
            loadingBar.visible = current.loading
            loadingBar.value = current.loadProgress / 100.0
            current.forceActiveFocus()
        }
    }

    function openAbout(kind) {
        var index = addTab()
        var view = viewAt(index)
        if (!view)
            return
        if (kind === "settings")
            view.loadHtml(bridge.settingsHtml(), "about:settings")
        else
            view.loadHtml(bridge.aboutHtml(), "about:version")
    }

    function closeTab(index) {
        if (tabs.count <= 1 || index < 0 || index >= tabs.count)
            return

        var previous = currentIndex
        var view = views[index]
        tabs.remove(index)
        views.splice(index, 1)
        if (view)
            view.destroy()

        for (let i = index; i < views.length; ++i) {
            if (views[i])
                views[i].tabIndex = i
        }

        if (index < previous)
            setCurrentIndex(previous - 1)
        else if (index === previous)
            setCurrentIndex(Math.min(index, tabs.count - 1))
    }

    function focusAddress() {
        navBar.focusAddress()
    }

    function navigate(text) {
        var target = currentView
        if (!target || text === "")
            return
        if (text === "about:version") {
            target.loadHtml(bridge.aboutHtml(), "about:version")
            return
        }
        if (text === "about:newtab") {
            target.loadHtml(bridge.newtabHtml(), "about:newtab")
            return
        }
        if (text === "about:settings") {
            target.loadHtml(bridge.settingsHtml(), "about:settings")
            return
        }
        target.url = bridge.resolveAddress(text)
    }

    Column {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: tabstripRow
            width: parent.width
            height: 40
            color: Theme.tabstripBg

            TabStrip {
                id: tabstrip
                anchors.left: parent.left
                anchors.leftMargin: 78
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                tabModel: tabs
                currentIndex: window.currentIndex
                onTabClicked: function (index) { window.setCurrentIndex(index) }
                onTabClosed: function (index) { window.closeTab(index) }
                onNewTabRequested: window.addTab()
                onBackgroundPressed: window.startSystemMove()
                onBackgroundDoubleClicked: window.toggleZoom()
            }

            AppMenu {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                windowRef: window
            }
        }

        Rectangle {
            width: parent.width
            height: 38
            color: Theme.toolbarBg

            Toolbar {
                id: navBar
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                address: window.address
                secureIcon: window.bridge.iconUrl("lock/lock.svg", Theme.textInactive)
                insecureIcon: window.bridge.iconUrl("lock/lock-open.svg", "")
                onBackRequested: if (window.currentView) window.currentView.goBack()
                onForwardRequested: if (window.currentView) window.currentView.goForward()
                onReloadRequested: if (window.currentView) window.currentView.reload()
                onStopRequested: if (window.currentView) window.currentView.stop()
                onAddressSubmitted: function (text) { window.navigate(text) }
            }
        }

        ProgressBar {
            id: loadingBar
            visible: false
            width: parent.width
            implicitHeight: 3
            indeterminate: false
            from: 0
            to: 1
            background: Rectangle { color: "transparent" }
            contentItem: Rectangle {
                color: Theme.progress
                width: loadingBar.visualPosition * loadingBar.width
                height: 3
            }
        }

        Item {
            id: contentArea
            width: parent.width
            height: parent.height - tabstripRow.height - 38 - 3
            clip: true
        }
    }

    LinkBar {
        id: linkBar
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 8
        anchors.bottomMargin: 8
    }

    Shortcut { sequences: ["Ctrl+T"]; onActivated: window.addTab() }
    Shortcut { sequences: ["Ctrl+W"]; onActivated: window.closeTab(window.currentIndex) }
    Shortcut { sequences: ["Ctrl+L"]; onActivated: window.focusAddress() }
    Shortcut { sequences: ["Ctrl+,"]; onActivated: window.openAbout("settings") }
    Shortcut { sequences: ["Ctrl+R"]; onActivated: if (window.currentView) window.currentView.reload() }
    Shortcut { sequences: ["Escape"]; onActivated: if (window.currentView) window.currentView.stop() }

    Component.onCompleted: addTab()
}
