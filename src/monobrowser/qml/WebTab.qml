import QtQuick
import QtWebEngine

WebEngineView {
    id: view

    property int tabIndex: -1
    property var pendingRequest: null
    property bool certificateError: false

    signal pageChanged()
    signal progressChanged()
    signal popupRequested()
    signal hoveredLink(string target)

    focus: true

    onUrlChanged: {
        certificateError = false
        pageChanged()
    }
    onTitleChanged: pageChanged()
    onIconChanged: pageChanged()
    onLoadingChanged: pageChanged()
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

    function videoProbeScript(playing) {
        return "(function () {" +
               " function pick(nodes) {" +
               "  for (var i = 0; i < nodes.length; ++i) {" +
               "   var v = nodes[i];" +
               "   if (v.videoWidth <= 0) continue;" +
               "   if (" + playing + " && (v.paused || v.ended)) continue;" +
               "   var r = v.getBoundingClientRect();" +
               "   if (r.width < 40 || r.height < 40) continue;" +
               "   return [r.x, r.y, r.width, r.height, v.ended ? 1 : 0];" +
               "  }" +
               "  return null;" +
               " }" +
               " var direct = pick(document.querySelectorAll('video'));" +
               " if (direct) return direct;" +
               " var all = document.querySelectorAll('*');" +
               " for (var j = 0; j < all.length; ++j) {" +
               "  var root = all[j].shadowRoot;" +
               "  if (!root) continue;" +
               "  var nested = pick(root.querySelectorAll('video'));" +
               "  if (nested) return nested;" +
               " }" +
               " return null;" +
               "})()"
    }

    function frameBoxesScript() {
        return "(function () {" +
               " var list = document.querySelectorAll('iframe');" +
               " var out = [];" +
               " for (var i = 0; i < list.length; ++i) {" +
               "  var r = list[i].getBoundingClientRect();" +
               "  out.push([list[i].src, r.x, r.y]);" +
               " }" +
               " return out;" +
               "})()"
    }

    function frameOffset(boxes, frame, index) {
        if (!boxes)
            return [0, 0]
        var url = String(frame.url)
        for (var i = 0; i < boxes.length; ++i) {
            if (String(boxes[i][0]) === url)
                return [boxes[i][1], boxes[i][2]]
        }
        if (index < boxes.length)
            return [boxes[index][1], boxes[index][2]]
        return [0, 0]
    }

    function probeFrame(frame, offsetX, offsetY, depth, playing, callback) {
        if (!frame || depth > probeDepthLimit) {
            callback(null)
            return
        }
        frame.runJavaScript(videoProbeScript(playing), function (rect) {
            if (rect !== null && rect !== undefined) {
                callback([rect[0] + offsetX, rect[1] + offsetY, rect[2], rect[3], rect[4], frame])
                return
            }
            var frames = frame.children
            if (!frames || frames.length === 0) {
                callback(null)
                return
            }
            frame.runJavaScript(frameBoxesScript(), function (boxes) {
                var pending = frames.length
                var found = null
                for (var i = 0; i < frames.length; ++i) {
                    var child = frames[i]
                    var offset = frameOffset(boxes, child, i)
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

    function scrollVideoIntoView(frame, callback) {
        if (!frame) {
            callback()
            return
        }
        frame.runJavaScript("(function () {" +
                            " var l = document.querySelectorAll('video');" +
                            " for (var i = 0; i < l.length; ++i) {" +
                            "  var v = l[i];" +
                            "  if (v.videoWidth <= 0 || v.paused || v.ended) continue;" +
                            "  v.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });" +
                            "  return true;" +
                            " }" +
                            " return false;" +
                            "})()", function () { callback() })
    }

    function probeVideo(callback, requirePlaying) {
        probeFrame(mainFrame, 0, 0, 0,
                   requirePlaying === undefined ? true : requirePlaying, callback)
    }

    function openPending(target) {
        if (pendingRequest === null || target === null)
            return
        pendingRequest.openInWebEngineView(target)
        pendingRequest = null
    }
}