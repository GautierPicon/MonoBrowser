import QtQuick
import ".."

Image {
    id: root

    property var bridge: null
    property string iconName: ""
    property color color: Theme.iconNormal
    property int size: 16

    width: root.size
    height: root.size
    sourceSize: Qt.size(root.size * Screen.devicePixelRatio, root.size * Screen.devicePixelRatio)
    source: root.bridge && root.iconName !== "" ? root.bridge.iconUrl(root.iconName, root.color.toString()) : ""
    fillMode: Image.PreserveAspectFit
}
