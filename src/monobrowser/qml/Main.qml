import QtQuick
import QtQuick.Controls
import QtWebEngine

ApplicationWindow {
    id: window
    width: 1200
    height: 800
    visible: true
    minimumWidth: 480
    minimumHeight: 320
    color: Theme.tabstripBg
    title: currentView && currentView.title !== "" ? currentView.title : "MonoBrowser"

    flags: Qt.Window | Qt.FramelessWindowHint

    ListModel { id: tabModel }

    property int currentIndex: -1
    property var views: []
    property var address: ""

    readonly property var currentView:
        currentIndex >= 0 && currentIndex < views.length ? views[currentIndex] : null

    function viewAt(index) {
        return index >= 0 && index < views.length ? views[index] : null
    }

    function setRole(index, role, value) {
        if (index < 0 || index >= tabModel.count)
            return
        if (typeof value !== "string")
            return
        tabModel.setProperty(index, role, value)
    }

    function addTab(url) {
        var view = createView()
        views.push(view)
        var target = url !== undefined && url !== null ? url : ""
        tabModel.append({
            title: "New Tab",
            url: target,
            favicon: ""
        })
        var index = tabModel.count - 1
        if (view) {
            if (target !== "")
                view.url = target
            else
                view.loadHtml(bridge.newtabHtml(), "about:newtab")
        }
        setCurrentIndex(index)
        if (index > 0)
            focusAddress()
        return index
    }

    function createView() {
        var component = Qt.createComponent("TabView.qml")
        if (component.status === Component.Error) {
            console.warn("TabView.qml:", component.errorString())
            return null
        }
        var view = component.createObject(contentArea)
        if (view === null)
            return null
        view.anchors.fill = contentArea
        view.tabIndex = views.length
        connectView(view)
        return view
    }

    function connectView(view) {
        view.pageChanged.connect(function () { syncView(view) })
        view.popupRequested.connect(function () {
            var index = addTab()
            view.openPending(views[index])
        })
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
            var query = bridge.internalParam(text)
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
        navBar.refreshHistory(view.canGoBack, view.canGoForward)
        navBar.loading = view.loading
        loadingBar.visible = view.loading
        loadingBar.value = view.loadProgress / 100.0
    }

    function setCurrentIndex(index) {
        if (index < 0 || index >= tabModel.count)
            return
        for (var i = 0; i < views.length; ++i) {
            var view = views[i]
            if (view)
                view.visible = i === index
        }
        currentIndex = index
        var current = currentView
        if (current) {
            var url = current.url.toString()
            address = url === "about:newtab" ? "" : url
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
        if (tabModel.count <= 1 || index < 0 || index >= tabModel.count)
            return

        var view = views[index]
        tabModel.remove(index)
        views.splice(index, 1)
        if (view)
            view.destroy()

        for (var i = index; i < views.length; ++i) {
            if (views[i])
                views[i].tabIndex = i
        }

        if (tabModel.count === 0)
            return
        var next = Math.min(index, tabModel.count - 1)
        setCurrentIndex(next)
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
                tabModel: tabModel
                currentIndex: window.currentIndex
                onTabClicked: function (index) { window.setCurrentIndex(index) }
                onTabClosed: function (index) { window.closeTab(index) }
                onNewTabRequested: window.addTab()
                onBackgroundPressed: window.startSystemMove()
            }

            AppMenu {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                windowRef: window
            }

            TrafficLights {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                windowActive: window.active
                onActivated: function (index) {
                    if (index === 0)
                        window.close()
                    else if (index === 1)
                        window.showMinimized()
                    else if (window.visibility === Window.Maximized)
                        window.showNormal()
                    else
                        window.showMaximized()
                }
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

    Shortcut { sequences: ["Ctrl+T"]; onActivated: window.addTab() }
    Shortcut { sequences: ["Ctrl+W"]; onActivated: window.closeTab(window.currentIndex) }
    Shortcut { sequences: ["Ctrl+L"]; onActivated: window.focusAddress() }
    Shortcut { sequences: ["Ctrl+R"]; onActivated: if (window.currentView) window.currentView.reload() }
    Shortcut { sequences: ["Escape"]; onActivated: if (window.currentView) window.currentView.stop() }

    ResizeGrip {
        edge: Qt.LeftEdge
        x: 0
        y: 0
        width: 6
        height: window.height
    }
    ResizeGrip {
        edge: Qt.RightEdge
        x: window.width - 6
        y: 0
        width: 6
        height: window.height
    }
    ResizeGrip {
        edge: Qt.TopEdge
        x: 0
        y: 0
        width: window.width
        height: 6
    }
    ResizeGrip {
        edge: Qt.BottomEdge
        x: 0
        y: window.height - 6
        width: window.width
        height: 6
    }
    ResizeGrip {
        edge: Qt.TopLeftCorner
        x: 0
        y: 0
        width: 12
        height: 12
    }
    ResizeGrip {
        edge: Qt.TopRightCorner
        x: window.width - 12
        y: 0
        width: 12
        height: 12
    }
    ResizeGrip {
        edge: Qt.BottomLeftCorner
        x: 0
        y: window.height - 12
        width: 12
        height: 12
    }
    ResizeGrip {
        edge: Qt.BottomRightCorner
        x: window.width - 12
        y: window.height - 12
        width: 12
        height: 12
    }

    Component.onCompleted: addTab()
}
