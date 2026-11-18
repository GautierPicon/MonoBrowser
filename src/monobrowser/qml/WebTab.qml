import QtQuick
import QtWebEngine

WebEngineView {
    id: view

    property int tabIndex: -1
    property var pendingRequest: null
    property bool certificateError: false
    property bool cosmeticCss: false

    readonly property string adblockCosmeticSource:
        "(function () {"
        + " function inject () {"
        + "   if (document.getElementById('adblock-cosmetic-style')) return true;"
        + "   var target = document.head || document.documentElement;"
        + "   if (!target) return false;"
        + "   var s = document.createElement('style');"
        + "   s.id = 'adblock-cosmetic-style';"
        + "   var c = 'iframe[src*=\"doubleclick.net\"],iframe[src*=\"googlesyndication.com\"],iframe[src*=\"googleadservices.com\"],iframe[src*=\"adservice.google.com\"],iframe[src*=\"amazon-adsystem.com\"],iframe[src*=\"adnxs.com\"],iframe[src*=\"taboola.com\"],iframe[src*=\"outbrain.com\"],ins.adsbygoogle,iframe[id^=\"aswift\"],iframe[id^=\"google_ads\"],div[id^=\"div-gpt-ad\"],div[id^=\"google_ad\"],.adsbygoogle,ins[data-ad-client]';"
        + "   s.textContent = c + '{display:none !important}';"
        + "   target.appendChild(s);"
        + "   return true;"
        + " }"
        + " if (!inject()) document.addEventListener('DOMContentLoaded', function () { inject(); });"
        + "})()"

    signal pageChanged()
    signal progressChanged()
    signal popupRequested()
    signal hoveredLink(string target)

    settings.playbackRequiresUserGesture: false

    focus: true

    onUrlChanged: {
        certificateError = false
        pageChanged()
    }
    onTitleChanged: pageChanged()
    onIconChanged: pageChanged()
    onLoadingChanged: {
        pageChanged()
        if (view.cosmeticCss)
            view.runJavaScript(view.adblockCosmeticSource)
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

    function videoProbeScript(playing) {
        return "(function () {" +
               " var strict = " + playing + ";" +
               " function styleVisible(v) {" +
               "  var cs = window.getComputedStyle(v);" +
               "  if (cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse') return false;" +
               "  var opacity = parseFloat(cs.opacity);" +
               "  if (!isNaN(opacity) && opacity <= 0) return false;" +
               "  return true;" +
               " }" +
               " function rectUsable(r) {" +
               "  if (r.width < 40 || r.height < 40) return false;" +
               "  return r.bottom > 0 && r.right > 0 && r.top < window.innerHeight && r.left < window.innerWidth;" +
               " }" +
               " function unoccluded(v, r) {" +
               "  var points = [[0.5, 0.5], [0.3, 0.3], [0.7, 0.3], [0.3, 0.7], [0.7, 0.7]];" +
               "  var evaluated = 0;" +
               "  for (var i = 0; i < points.length; ++i) {" +
               "   var x = r.left + r.width * points[i][0];" +
               "   var y = r.top + r.height * points[i][1];" +
               "   var el = document.elementFromPoint(x, y);" +
               "   if (!el) continue;" +
               "   evaluated++;" +
               "   if (el === v || el.contains(v)) return true;" +
               "  }" +
               "  return evaluated === 0;" +
               " }" +
               " function audible(v) { return !v.muted && v.volume > 0; }" +
               " function consider(nodes, best) {" +
               "  for (var i = 0; i < nodes.length; ++i) {" +
               "   var v = nodes[i];" +
               "   if (v.videoWidth <= 0) continue;" +
               "   if (strict && (v.paused || v.ended)) continue;" +
               "   var r = v.getBoundingClientRect();" +
               "   if (!rectUsable(r)) continue;" +
               "   if (!styleVisible(v)) continue;" +
               "   if (!unoccluded(v, r)) continue;" +
               "   var score = r.width * r.height * (audible(v) ? 4 : 1);" +
               "   if (best === null || score > best.score)" +
               "    best = { score: score," +
               "             rect: [r.x, r.y, r.width, r.height, v.ended ? 1 : 0, v.paused ? 1 : 0," +
               "                    v.currentTime || 0, isFinite(v.duration) ? v.duration : 0] };" +
               "  }" +
               "  return best;" +
               " }" +
               " var best = consider(document.querySelectorAll('video'), null);" +
               " if (!best) {" +
               "  var all = document.querySelectorAll('*');" +
               "  for (var j = 0; j < all.length; ++j) {" +
               "   var root = all[j].shadowRoot;" +
               "   if (!root) continue;" +
               "   best = consider(root.querySelectorAll('video'), best);" +
               "  }" +
               " }" +
               " return best ? best.rect : null;" +
               "})()"
    }

    function frameBoxesScript() {
        return "(function () {" +
               " var list = document.querySelectorAll('iframe');" +
               " var out = [];" +
               " for (var i = 0; i < list.length; ++i) {" +
               "  var r = list[i].getBoundingClientRect();" +
               "  var cs = window.getComputedStyle(list[i]);" +
               "  var hidden = (r.width <= 0 || r.height <= 0 || cs.display === 'none' || cs.visibility === 'hidden') ? 1 : 0;" +
               "  out.push([list[i].src, r.x, r.y, hidden]);" +
               " }" +
               " return out;" +
               "})()"
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

    function probeFrame(frame, offsetX, offsetY, depth, playing, callback) {
        if (!frame || depth > probeDepthLimit) {
            callback(null)
            return
        }
        frame.runJavaScript(videoProbeScript(playing), function (rect) {
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
            frame.runJavaScript(frameBoxesScript(), function (boxes) {
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

    function pipPauseScript() {
        return "(function () {" +
               " var l = document.querySelectorAll('video');" +
               " for (var i = 0; i < l.length; ++i) {" +
               "  var v = l[i];" +
               "  if (v.videoWidth > 0 && !v.paused) v.pause();" +
               " }" +
               "})()"
    }

    function pipTogglePlaybackScript() {
        return "(function () {" +
               " var l = document.querySelectorAll('video');" +
               " for (var i = 0; i < l.length; ++i) {" +
               "  var v = l[i];" +
               "  if (v.videoWidth <= 0) continue;" +
               "  if (v.paused) v.play(); else v.pause();" +
               "  return true;" +
               " }" +
               " return false;" +
               "})()"
    }

    function pipSeekScript(ratio) {
        var clamped = Math.max(0, Math.min(1, ratio))
        return "(function () {" +
               " var l = document.querySelectorAll('video');" +
               " for (var i = 0; i < l.length; ++i) {" +
               "  var v = l[i];" +
               "  if (v.videoWidth <= 0) continue;" +
               "  if (isFinite(v.duration) && v.duration > 0) v.currentTime = v.duration * " + clamped + ";" +
               "  return true;" +
               " }" +
               " return false;" +
               "})()"
    }

    function pipHidePlayerChromeScript() {
        var rules = "#movie_player .ytp-chrome-top," +
            "#movie_player .ytp-chrome-bottom," +
            "#movie_player .ytp-overlays-container," +
            "#movie_player .ytp-watermark," +
            "#movie_player .ytp-large-play-button," +
            ".video-js .vjs-big-play-button," +
            ".video-js .vjs-control-bar," +
            ".jwplayer .jw-controlbar," +
            ".jwplayer .jw-title," +
            ".plyr .plyr__control--overlaid," +
            ".plyr .plyr__controls," +
            ".mejs__controls," +
            ".mejs__overlay" +
            "{visibility:hidden !important}";
        return "(function () {" +
               " var style = document.getElementById('monobrowser-pip-chrome');" +
               " if (!style) {" +
               "  style = document.createElement('style');" +
               "  style.id = 'monobrowser-pip-chrome';" +
               "  style.textContent = '" + rules + "';" +
               "  (document.head || document.documentElement).appendChild(style);" +
               " }" +
               "})()"
    }

    function pipShowPlayerChromeScript() {
        return "(function () {" +
               " var style = document.getElementById('monobrowser-pip-chrome');" +
               " if (style) style.remove();" +
               "})()"
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
        pendingRequest.openIn(target)
        pendingRequest = null
    }
}