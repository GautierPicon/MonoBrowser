import QtQuick
import "chrome"
import "pip"
import "tabs"

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

    property var bridge: null

    readonly property var views: tabManager.views
    readonly property int currentIndex: tabManager.currentIndex
    readonly property var currentView: tabManager.currentView
    readonly property bool canPip: pipController.canPip
    readonly property int closedCount: tabManager.closedCount

    function addTab() { return tabManager.addTab() }
    function closeTab(index) { tabManager.closeTab(index) }
    function setCurrentIndex(index) { tabManager.setCurrentIndex(index) }
    function updateVisibility() { tabManager.updateVisibility() }
    function updateLifecycle(view) { tabManager.updateLifecycle(view) }
    function reopenClosedTab() { tabManager.reopenClosedTab() }
    function openAbout(kind) { tabManager.openAbout(kind) }
    function togglePip() { pipController.togglePip() }

    function toggleZoom() {
        if (visibility === Window.Maximized || visibility === Window.FullScreen)
            showNormal()
        else
            showMaximized()
    }

    BrowserChrome {
        id: chrome
        anchors.fill: parent
        tabModel: tabManager.tabsModel
        currentIndex: tabManager.currentIndex
        address: tabManager.address
        bridge: window.bridge
        windowRef: window
        canPip: window.canPip
        pipActive: pipController.pipView !== null
        swipeView: tabManager.currentView
        pipDetached: pipController.pipView !== null && pipController.pipView === tabManager.currentView
        pipSnapshot: pipController.pipSnapshot
        pipVideoFrac: pipController.pipVideoFrac
        onTabClicked: function (index) { tabManager.setCurrentIndex(index) }
        onFaviconError: function (index) { tabManager.setRole(index, "favicon", "") }
        onTabClosed: function (index) { tabManager.closeTab(index) }
        onTabMoved: function (from, to) { tabManager.moveTab(from, to) }
        onTabMuteToggled: function (index) { tabManager.toggleTabMute(index) }
        onNewTabRequested: tabManager.addTab()
        onBackgroundPressed: window.startSystemMove()
        onBackgroundDoubleClicked: window.toggleZoom()
        onAddressSubmitted: function (text) { tabManager.navigate(text) }
        onBackRequested: if (window.currentView) window.currentView.goBack()
        onForwardRequested: if (window.currentView) window.currentView.goForward()
        onReloadRequested: tabManager.reloadCurrent()
        onStopRequested: if (window.currentView) window.currentView.stop()
        onPipRequested: window.togglePip()
    }

    readonly property var navBar: chrome.navBar
    readonly property var loadingBar: chrome.loadingBar
    readonly property var linkBar: chrome.linkBar
    readonly property var findBar: chrome.findBar
    readonly property var zoomHud: chrome.zoomHud
    readonly property Item contentArea: chrome.contentArea

    Shortcut { sequences: ["Meta+T"]; onActivated: tabManager.addTab() }
    Shortcut { sequences: ["Meta+W"]; onActivated: tabManager.closeTab(tabManager.currentIndex) }
    Shortcut { sequences: ["Meta+L"]; onActivated: tabManager.focusAddress() }
    Shortcut { sequences: ["Meta+Comma"]; onActivated: tabManager.openAbout("settings") }
    Shortcut { sequences: ["Meta+R"]; onActivated: tabManager.reloadCurrent() }
    Shortcut { sequences: ["Meta+Alt+Left"]; onActivated: tabManager.cycleTab(-1) }
    Shortcut { sequences: ["Meta+Alt+Right"]; onActivated: tabManager.cycleTab(1) }
    Shortcut { sequences: ["Meta+Shift+P"]; onActivated: window.togglePip() }
    Shortcut { sequences: ["Meta+Shift+M"]; onActivated: tabManager.toggleTabMute(tabManager.currentIndex) }
    Shortcut { sequences: ["Escape"]; onActivated: if (window.findBar.visible) window.findBar.close(); else if (window.currentView) window.currentView.stop() }
    Shortcut { sequences: ["Meta+F"]; onActivated: window.findBar.toggle() }
    Shortcut { sequences: ["Meta+Shift+BracketLeft"]; onActivated: tabManager.cycleTab(-1) }
    Shortcut { sequences: ["Meta+Shift+BracketRight"]; onActivated: tabManager.cycleTab(1) }
    Shortcut { sequences: ["Meta+Shift+T"]; onActivated: tabManager.reopenClosedTab() }
    Shortcut { sequences: ["Meta+=", "Meta+Plus"]; onActivated: tabManager.zoomChange(0.1) }
    Shortcut { sequences: ["Meta+-", "Meta+Minus"]; onActivated: tabManager.zoomChange(-0.1) }
    Shortcut { sequences: ["Meta+0"]; onActivated: tabManager.zoomReset() }

    Connections {
        target: window.bridge
        function onThemeModeChanged() {
            Theme.mode = window.bridge.themeMode
            tabManager.reloadAboutPages()
        }
        function onAdblockEnabledChanged() {
            tabManager.syncAdblockCosmetic()
        }
        function onAdblockCosmeticChanged() {
            tabManager.syncAdblockCosmetic()
        }
    }

    Connections {
        target: Qt.styleHints
        function onColorSchemeChanged() { // qmllint disable missing-property
            if (window.bridge && window.bridge.themeMode === "system")
                tabManager.reloadAboutPages()
        }
    }

    PipWindow {
        id: pipWindowItem
        bridge: window.bridge
        onExitRequested: pipController.exitPip()
        onMinimizeRequested: pipController.exitPip()
        onCloseRequested: pipController.closePip()
        onBackToPageRequested: pipController.exitPip()
        onPlayPauseRequested: pipController.togglePipPlayback()
        onSeekRequested: function (ratio) { pipController.seekPip(ratio) }
    }

    PipController {
        id: pipController
        host: window
        pipWindow: pipWindowItem
    }

    TabManager {
        id: tabManager
        host: window
        controller: pipController
    }

    onActiveChanged: pipController.updatePipAvailability()
    onClosing: {
        pipController.exitPip()
        tabManager.saveSessionState()
    }

    Component.onCompleted: {
        if (bridge) {
            Theme.mode = bridge.themeMode
        }
        tabManager.syncAdblockCosmetic()
        tabManager.restoreSessionOrNewTab()
    }
}
