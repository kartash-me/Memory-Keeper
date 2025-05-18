/* global ymaps */

function createMap(containerId, photosUrl) {
    ymaps.ready(() => {
        const map = new ymaps.Map(containerId, {center: [20, 0], zoom: 2});
        const template = getBalloonTemplate()

        fetch(photosUrl)
            .then(response => response.json())
            .then(photos => {
                if (!photos.length) {
                    return;
                }

                const clusterer = new ymaps.Clusterer({
                    preset: "islands#invertedOrangeClusterIcons"
                });

                const coordsForBounds = photos.map(photo => {
                    const placemark = createPlacemark(photo, template);
                    clusterer.add(placemark);
                    return [photo.lat, photo.lon];
                });

                map.geoObjects.add(clusterer);
                adjustMapView(map, coordsForBounds);
            })
            .catch(err => console.error("Failed to load geo-data", err));
    });
}

function getBalloonTemplate() {
    const container = document.getElementById("balloon-container");
    return container ? container.innerHTML : null;
}

function createPlacemark(photo, template) {
    return new ymaps.Placemark(
        [photo.lat, photo.lon],
        {
            balloonContent: getBalloonContent(photo, template)
        },
        {
            iconLayout: "default#image",
            iconImageHref: photo.thumb,
            iconImageSize: [48, 48],
            iconImageOffset: [-24, -24]
        }
    );
}

function getBalloonContent(photo, template) {
    return template
        .replace("{ full }", photo.full)
        .replace("{ address }", photo.address ?? "")
        .replace("{ timestamp }", photo.timestamp
            ? new Date(photo.timestamp).toLocaleString()
            : "")
        .replace("{ description }", photo.description ?? "");
}

function adjustMapView(map, coords) {
    if (coords.length === 1) {
        map.setCenter(coords[0], 12);
    } else {
        map.setBounds(coords, {checkZoomRange: true, zoomMargin: 50});
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById("map");
    if (mapContainer) {
        createMap("map", mapContainer.dataset.photosUrl);
    }
});
