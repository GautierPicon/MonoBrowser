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

    function openPending(target) {
        if (pendingRequest === null || target === null)
            return
        pendingRequest.openInWebEngineView(target)
        pendingRequest = null
    }
}