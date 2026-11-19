import QtQuick
import QtWebEngine
import "scripts/pageScripts.js" as PageScripts

WebEngineView {
    id: view

    property int tabIndex: -1
    property var pendingRequest: null
    property bool certificateError: false
    property bool cosmeticCss: false
    property string historyIconHref: ""

    signal pageChanged()
    signal progressChanged()
    signal popupRequested()
    signal hoveredLink(string target)

    settings.playbackRequiresUserGesture: false

    focus: true

    onUrlChanged: {
        certificateError = false
        historyIconHref = ""
        pageChanged()
    }
    onTitleChanged: pageChanged()
    onIconChanged: pageChanged()
    onLoadingChanged: {
        pageChanged()
        if (view.cosmeticCss)
            view.runJavaScript(PageScripts.adblockCosmeticScript())
    }
    onLoadProgressChanged: progressChanged()
    onLinkHovered: function (url) { hoveredLink(url.toString()) }

    onCertificateError: function (error) {
        certificateError = true
        error.rejectCertificate()
    }

    onNewWindowRequested: function (request) {
        pendingRequest = request
        popupRequested()
    }

    readonly property int probeDepthLimit: 4

    function probeFrame(frame, offsetX, offsetY, depth, playing, callback) {
        if (!frame || depth > probeDepthLimit) {
            callback(null)
            return
        }
        frame.runJavaScript(PageScripts.videoProbeScript(playing), function (rect) {
            if (rect !== null && rect !== undefined) {
                callback([rect[0] + offsetX, rect[1] + offsetY, rect[2], rect[3], rect[4], frame,
                          rect[5], rect[6], rect[7]])
                return
            }
            var frames = frame.children
            if (!frames || frames.length === 0) {
                callback(null)
                return
            }
            frame.runJavaScript(PageScripts.frameBoxesScript(), function (boxes) {
                var pending = frames.length
                var found = null
                for (let i = 0; i < frames.length; ++i) {
                    let child = frames[i]
                    let offset = frameOffset(boxes, child, i)
                    if (offset[2] === 1) {
                        if (--pending === 0)
                            callback(found)
                        continue
                    }
                    probeFrame(child, offsetX + offset[0], offsetY + offset[1], depth + 1,
                               playing, function (result) {
                        if (result !== null && result !== undefined && found === null)
                            found = result
                        if (--pending === 0)
                            callback(found)
                    })
                }
            })
        })
    }

    function frameOffset(boxes, frame, index) {
        if (!boxes)
            return [0, 0, 0]
        var url = String(frame.url).replace(/#.*$/, "").replace(/\/$/, "")
        for (let i = 0; i < boxes.length; ++i) {
            if (String(boxes[i][0]).replace(/#.*$/, "").replace(/\/$/, "") === url)
                return [boxes[i][1], boxes[i][2], boxes[i][3] === 1 ? 1 : 0]
        }
        if (index < boxes.length)
            return [boxes[index][1], boxes[index][2], boxes[index][3] === 1 ? 1 : 0]
        return [0, 0, 0]
    }

    function pipPauseScript() {
        return PageScripts.pipPauseScript()
    }

    function pipTogglePlaybackScript() {
        return PageScripts.pipTogglePlaybackScript()
    }

    function pipSeekScript(ratio) {
        return PageScripts.pipSeekScript(ratio)
    }

    function pipHidePlayerChromeScript() {
        return PageScripts.pipHidePlayerChromeScript()
    }

    function pipShowPlayerChromeScript() {
        return PageScripts.pipShowPlayerChromeScript()
    }

    function scrollVideoIntoView(frame, callback) {
        if (!frame) {
            callback()
            return
        }
        frame.runJavaScript(PageScripts.scrollVideoIntoViewScript(), function () { callback() })
    }

    function probeVideo(callback, requirePlaying) {
        probeFrame(mainFrame, 0, 0, 0,
                   requirePlaying === undefined ? true : requirePlaying, callback)
    }

    function openPending(target) {
        if (pendingRequest === null || target === null)
            return
        pendingRequest.openIn(target)
        pendingRequest = null
    }
}
