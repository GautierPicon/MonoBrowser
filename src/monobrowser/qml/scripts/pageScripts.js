function videoProbeScript(playing) {
  return `(function () {
 var strict = ${playing};
 function styleVisible(v) {
  var cs = window.getComputedStyle(v);
  if (cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse') return false;
  var opacity = parseFloat(cs.opacity);
  if (!isNaN(opacity) && opacity <= 0) return false;
  return true;
 }
 function rectUsable(r) {
  if (r.width < 40 || r.height < 40) return false;
  return r.bottom > 0 && r.right > 0 && r.top < window.innerHeight && r.left < window.innerWidth;
 }
 function unoccluded(v, r) {
  var points = [[0.5, 0.5], [0.3, 0.3], [0.7, 0.3], [0.3, 0.7], [0.7, 0.7]];
  var evaluated = 0;
  for (var i = 0; i < points.length; ++i) {
   var x = r.left + r.width * points[i][0];
   var y = r.top + r.height * points[i][1];
   var el = document.elementFromPoint(x, y);
   if (!el) continue;
   evaluated++;
   if (el === v || el.contains(v)) return true;
  }
  return evaluated === 0;
 }
 function audible(v) { return !v.muted && v.volume > 0; }
 function consider(nodes, best) {
  for (var i = 0; i < nodes.length; ++i) {
   var v = nodes[i];
   if (v.videoWidth <= 0) continue;
   if (strict && (v.paused || v.ended)) continue;
   var r = v.getBoundingClientRect();
   if (!rectUsable(r)) continue;
   if (!styleVisible(v)) continue;
   if (!unoccluded(v, r)) continue;
   var score = r.width * r.height * (audible(v) ? 4 : 1);
   if (best === null || score > best.score)
    best = { score: score,
             rect: [r.x, r.y, r.width, r.height, v.ended ? 1 : 0, v.paused ? 1 : 0,
                    v.currentTime || 0, isFinite(v.duration) ? v.duration : 0] };
  }
  return best;
 }
 var best = consider(document.querySelectorAll('video'), null);
 if (!best && document.documentElement) {
  var walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_ELEMENT);
  while (walker.nextNode()) {
   var root = walker.currentNode.shadowRoot;
   if (!root) continue;
   best = consider(root.querySelectorAll('video'), best);
   if (best) break;
  }
 }
 return best ? best.rect : null;
})()`;
}
function frameBoxesScript() {
  return `(function () {
 var list = document.querySelectorAll('iframe');
 var out = [];
 for (var i = 0; i < list.length; ++i) {
  var r = list[i].getBoundingClientRect();
  var cs = window.getComputedStyle(list[i]);
  var hidden = (r.width <= 0 || r.height <= 0 || cs.display === 'none' || cs.visibility === 'hidden') ? 1 : 0;
  out.push([list[i].src, r.x, r.y, hidden]);
 }
 return out;
})()`;
}
function scrollVideoIntoViewScript() {
  return `(function () {
 var l = document.querySelectorAll('video');
 for (var i = 0; i < l.length; ++i) {
  var v = l[i];
  if (v.videoWidth <= 0 || v.paused || v.ended) continue;
  v.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
  return true;
 }
 return false;
})()`;
}
function pipPauseScript() {
  return `(function () {
 var l = document.querySelectorAll('video');
 for (var i = 0; i < l.length; ++i) {
  var v = l[i];
  if (v.videoWidth > 0 && !v.paused) v.pause();
 }
})()`;
}
function pipTogglePlaybackScript() {
  return `(function () {
 var l = document.querySelectorAll('video');
 for (var i = 0; i < l.length; ++i) {
  var v = l[i];
  if (v.videoWidth <= 0) continue;
  if (v.paused) v.play(); else v.pause();
  return true;
 }
 return false;
})()`;
}
function pipSeekScript(ratio) {
  const clamped = Math.max(0, Math.min(1, ratio));
  return `(function () {
 var l = document.querySelectorAll('video');
 for (var i = 0; i < l.length; ++i) {
  var v = l[i];
  if (v.videoWidth <= 0) continue;
  if (isFinite(v.duration) && v.duration > 0) v.currentTime = v.duration * ${clamped};
  return true;
 }
 return false;
})()`;
}
function pipHidePlayerChromeScript() {
  const rules = "#movie_player .ytp-chrome-top,#movie_player .ytp-chrome-bottom,#movie_player .ytp-overlays-container,#movie_player .ytp-watermark,#movie_player .ytp-large-play-button,.video-js .vjs-big-play-button,.video-js .vjs-control-bar,.jwplayer .jw-controlbar,.jwplayer .jw-title,.plyr .plyr__control--overlaid,.plyr .plyr__controls,.mejs__controls,.mejs__overlay{visibility:hidden !important}";
  return `(function () {
 var style = document.getElementById('monobrowser-pip-chrome');
 if (!style) {
  style = document.createElement('style');
  style.id = 'monobrowser-pip-chrome';
  style.textContent = '${rules}';
  (document.head || document.documentElement).appendChild(style);
 }
})()`;
}
function pipShowPlayerChromeScript() {
  return `(function () {
 var style = document.getElementById('monobrowser-pip-chrome');
 if (style) style.remove();
})()`;
}
function adblockCosmeticScript() {
  return `(function () {
 function inject () {
   if (document.getElementById('adblock-cosmetic-style')) return true;
   var target = document.head || document.documentElement;
   if (!target) return false;
   var s = document.createElement('style');
   s.id = 'adblock-cosmetic-style';
   var c = 'iframe[src*="doubleclick.net"],iframe[src*="googlesyndication.com"],iframe[src*="googleadservices.com"],iframe[src*="adservice.google.com"],iframe[src*="amazon-adsystem.com"],iframe[src*="adnxs.com"],iframe[src*="taboola.com"],iframe[src*="outbrain.com"],ins.adsbygoogle,iframe[id^="aswift"],iframe[id^="google_ads"],div[id^="div-gpt-ad"],div[id^="google_ad"],.adsbygoogle,ins[data-ad-client]';
   s.textContent = c + '{display:none !important}';
   target.appendChild(s);
   return true;
 }
 if (!inject()) document.addEventListener('DOMContentLoaded', function () { inject(); });
})()`;
}
function iconLinkScript() {
  return "(function () { var links = document.querySelectorAll('link[rel~=icon], link[rel=shortcut-icon], link[rel=icon], link[rel=apple-touch-icon]'); if (!links.length) return ''; var best = links[0]; var bestSize = -1; for (var i = 0; i < links.length; i++) { var s = links[i].getAttribute('sizes'); var m = s ? s.match(/(\\d+)\\s*x\\s*(\\d+)/) : null; var w = m ? parseInt(m[1], 10) : 10; if (w > bestSize) { bestSize = w; best = links[i]; } } return best.href || ''; })()";
}
function edgeProbeJs(back, x, y) {
  return "(function (back, x, y) { function atEdge (el) {   var max = el.scrollWidth - el.clientWidth;   if (max <= 1) return true;   var sl = Math.abs(el.scrollLeft);   return back ? sl < 1 : (max - sl) < 1; } function contained (style) {   var obx = String(style.getPropertyValue('overscroll-behavior-x') || style.getPropertyValue('overscroll-behavior') || '').toLowerCase();   return obx.indexOf('contain') !== -1 || obx.indexOf('none') !== -1; } function blockedElsewhere (style, el) {   var ox = String(style.overflowX || '').toLowerCase();   var scrollable = (ox === 'auto' || ox === 'scroll' || ox === 'overlay') && el.scrollWidth > el.clientWidth + 1;   return scrollable && !atEdge(el); } var el = document.elementFromPoint(x, y); while (el && el.nodeType === 1) {   var style = getComputedStyle(el);   if (contained(style)) return 'contained';   if (blockedElsewhere(style, el)) return 'scroller';   el = el.parentElement; } var root = document.scrollingElement || document.documentElement; if (root) {   if (contained(getComputedStyle(root))) return 'contained';   if (root.scrollWidth > root.clientWidth + 1 && !atEdge(root)) return 'scroller'; } return 'edge';})(" + back + ", " + Math.round(x) + ", " + Math.round(y) + ")";
}
