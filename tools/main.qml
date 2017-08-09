import QtQuick 2.7
import QtQuick.Window 2.2
import QtLocation 5.7
import QtPositioning 5.7


Window {
    property var pos: QtPositioning.coordinate(56.88614457563706, 24.20416950429917)
    property var wind: {
        direction: null
        speed: 0
    }

    width: 1600
    height: 1200
    visible: true

    Plugin {
        id: osmPlugin
        name: 'osm'
    }

    Row {
        id: row
        anchors.fill: parent

        Map {
            id: map
            anchors.fill: parent
            copyrightsVisible: false
            plugin: osmPlugin
            center: QtPositioning.coordinate(56.88614457563706, 24.20416950429917)
            activeMapType: supportedMapTypes[MapType.TerrainMap]
            zoomLevel: 19

            MapQuickItem {
                id: marker
                sourceItem: Image{
                    id: image
                    source: 'arrow.png'

                }
                coordinate: pos
                anchorPoint.x: image.width / 2
                anchorPoint.y: image.height / 2
            }

            onZoomLevelChanged: {
                marker.coordinate = pos
            }

            onCenterChanged: {
                marker.coordinate = pos
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onPressed: {
                    if (mouse.button & Qt.RightButton) {
                        pos = map.toCoordinate(Qt.point(mouse.x, mouse.y))
                        console.log('Setting new position:', pos.latitude, pos.longitude)
                        marker.coordinate = pos
                    }
                }
            }
        }

        Column {
            id: textColumn
            width: 200
            height: 400

            Text {
                id: posLatitudeText
                text: qsTr("Latitude: " + pos.latitude.toString())
                font.pixelSize: 12
            }

            Text {
                id: posLongitudeText
                text: qsTr("Longitude: " + pos.longitude.toString())
                font.pixelSize: 12
            }
        }
    }
}