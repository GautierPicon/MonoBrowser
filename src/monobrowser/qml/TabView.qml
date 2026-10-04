import QtQuick
import QtWebEngine

WebEngineView {
    id: view

    property int tabIndex: -1
    property var pendingRequest: null

    signal pageChanged()
    signal popupRequested()

    focus: true

    onUrlChanged: pageChanged()
    onTitleChanged: pageChanged()
    onIconChanged: pageChanged()
    onLoadingChanged: pageChanged()
    onLoadProgressChanged: pageChanged()

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