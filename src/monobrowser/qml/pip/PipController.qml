import QtQuick

Item {
    id: root

    property var host: null
    property var pipWindow: null

    property var pipView: null
    property var pipFrame: null
    property int pipProbeMisses: 0
    property int pipProbeCooldown: 0
    property var pipSnapshot: null
    property rect pipVideoFrac: Qt.rect(0, 0, 1, 1)
    property bool canPip: false

    width: 0
    height: 0

    readonly property var currentView: host ? host.currentView : null

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
        const area = host ? host.contentArea : null
        if (!area)
            return false
        return rect[0] >= -2 && rect[1] >= -2
            && rect[0] + rect[2] <= area.width + 2
            && rect[1] + rect[3] <= area.height + 2
    }

    function injectPipPlayerChrome(frame, on, view) {
        if (!view)
            return
        if (frame === null || frame === undefined)
            frame = view.mainFrame
        if (!frame)
            return
        const script = on ? view.pipHidePlayerChromeScript() : view.pipShowPlayerChromeScript()
        try {
            frame.runJavaScript(script, function () {})
        } catch (e) {
            console.warn("PipController: failed to inject player chrome", e)
        }
        const children = frame.children
        if (!children)
            return
        for (let i = 0; i < children.length; ++i)
            injectPipPlayerChrome(children[i], on, view)
    }

    function attachPip(view, rect) {
        if (!host || !host.contentArea || pipView === view || view !== currentView)
            return
        if (pipView !== null)
            exitPip()
        const frame = rect[5]
        injectPipPlayerChrome(frame, true, view)
        const area = host.contentArea
        var fracW = Math.max(1, area.width)
        var fracH = Math.max(1, area.height)
        pipVideoFrac = Qt.rect(
            Math.max(0, rect[0] / fracW),
            Math.max(0, rect[1] / fracH),
            Math.min(1, rect[2] / fracW),
            Math.min(1, rect[3] / fracH))
        try {
            view.grabToImage(function (result) {
                pipSnapshot = result.url
                pipView = view
                pipFrame = frame
                pipWindow.open(view, area, {
                    x: rect[0],
                    y: rect[1],
                    width: rect[2],
                    height: rect[3]
                })
                host.updateVisibility()
                host.updateLifecycle(view)
                host.linkBar.target = ""
            })
        } catch (e) {
            console.warn("PipController: failed to grab tab snapshot", e)
        }
    }

    function closePip() {
        const view = pipView
        const frame = pipFrame
        if (view && frame) {
            try {
                frame.runJavaScript(view.pipPauseScript(), function () {})
            } catch (e) {
                console.warn("PipController: failed to pause video", e)
            }
        }
        exitPip()
    }

    function togglePipPlayback() {
        const view = pipView
        const frame = pipFrame
        if (!view || !frame)
            return
        try {
            frame.runJavaScript(view.pipTogglePlaybackScript(), function () {})
            pipWindow.playing = !pipWindow.playing
        } catch (e) {
            console.warn("PipController: failed to toggle playback", e)
        }
    }

    function seekPip(ratio) {
        const view = pipView
        const frame = pipFrame
        if (!view || !frame)
            return
        try {
            frame.runJavaScript(view.pipSeekScript(ratio), function () {})
        } catch (e) {
            console.warn("PipController: failed to seek", e)
        }
    }

    function exitPip() {
        if (pipView === null)
            return
        const view = pipView
        const frame = pipFrame
        injectPipPlayerChrome(frame, false, view)
        pipView = null
        pipFrame = null
        pipSnapshot = null
        pipWindow.release()
        host.raise()
        host.requestActivate()
        host.updateVisibility()
        host.updateLifecycle(view)
        const index = host.views.indexOf(view)
        if (index >= 0 && index !== host.currentIndex)
            host.setCurrentIndex(index)
        else if (view === currentView)
            view.forceActiveFocus()
        updatePipAvailability()
    }

    function applyPipRect(view, rect) {
        if (view !== pipView)
            return
        pipFrame = rect[5]
        const duration = rect.length > 8 && isFinite(rect[8]) ? rect[8] : 0
        const currentTime = rect.length > 7 && isFinite(rect[7]) ? rect[7] : 0
        const paused = rect.length > 6 && rect[6] === 1
        pipWindow.playing = !paused
        pipWindow.duration = duration
        pipWindow.progressRatio = duration > 0 ? currentTime / duration : 0
        pipWindow.setVideoRect({
            x: rect[0],
            y: rect[1],
            width: rect[2],
            height: rect[3]
        })
    }

    function refreshPip() {
        const view = pipView
        if (view === null)
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
        const view = currentView
        if (pipView !== null || !view || !host || !host.active) {
            canPip = false
            return
        }
        if (pipProbeCooldown > 0) {
            pipProbeCooldown--
            return
        }
        view.probeVideo(function (rect) {
            const found = rect !== null && rect !== undefined
            if (view === currentView && pipView === null)
                canPip = found
            if (found) {
                pipProbeMisses = 0
                return
            }
            pipProbeMisses++
            if (pipProbeMisses >= 5) {
                pipProbeMisses = 0
                pipProbeCooldown = 3
            }
        })
    }

    Timer {
        interval: 1000
        repeat: true
        running: root.pipView !== null
        onTriggered: root.refreshPip()
    }

    Timer {
        interval: 1200
        repeat: true
        running: root.host ? root.host.active && root.pipView === null : false
        onTriggered: root.updatePipAvailability()
    }
}
