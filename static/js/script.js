// static/js/script.js
let map;
let marker;
let geocoder;
let infoWindow;

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the create card page
    const locationInput = document.getElementById('location');
    if (locationInput) {
        initializeLocationSearch();
    }

    // Check if we're on the view card page
    const mapDiv = document.getElementById('map');
    if (mapDiv) {
        // Load Google Maps API
        loadGoogleMapsScript();
    }
});

function loadGoogleMapsScript() {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY&libraries=places&callback=initMap`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
}

function initializeLocationSearch() {
    loadGoogleMapsScript();

    const locationInput = document.getElementById('location');
    const mapContainer = document.createElement('div');
    mapContainer.id = 'map';
    mapContainer.style.height = '200px';
    mapContainer.style.marginTop = '1rem';

    locationInput.parentNode.appendChild(mapContainer);

    // Create location button
    const locationButton = document.createElement('button');
    locationButton.type = 'button';
    locationButton.innerHTML = '<i class="fas fa-location-arrow"></i>';
    locationButton.className = 'location-button';
    locationInput.parentNode.appendChild(locationButton);

    locationButton.addEventListener('click', () => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const pos = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    };

                    if (marker) {
                        marker.setPosition(pos);
                    }
                    map.setCenter(pos);

                    // Reverse geocode to get address
                    geocoder.geocode({ location: pos }, (results, status) => {
                        if (status === 'OK') {
                            if (results[0]) {
                                locationInput.value = results[0].formatted_address;
                            }
                        }
                    });
                },
                () => {
                    alert('Error: The Geolocation service failed.');
                }
            );
        } else {
            alert('Error: Your browser doesn\'t support geolocation.');
        }
    });
}

function initMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;

    geocoder = new google.maps.Geocoder();

    // Initialize map with default center
    map = new google.maps.Map(mapDiv, {
        zoom: 15,
        center: { lat: 0, lng: 0 },
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });

    // Initialize info window
    infoWindow = new google.maps.InfoWindow();

    // If we're on the create card page
    const locationInput = document.getElementById('location');
    if (locationInput) {
        // Initialize autocomplete
        const autocomplete = new google.maps.places.Autocomplete(locationInput);
        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.geometry) return;

            // Update map
            map.setCenter(place.geometry.location);
            if (marker) {
                marker.setPosition(place.geometry.location);
            } else {
                marker = new google.maps.Marker({
                    map: map,
                    position: place.geometry.location,
                    draggable: true
                });
            }
        });

        // Initialize marker
        marker = new google.maps.Marker({
            map: map,
            draggable: true
        });

        // Handle marker drag events
        marker.addListener('dragend', () => {
            const position = marker.getPosition();
            geocoder.geocode({ location: position }, (results, status) => {
                if (status === 'OK') {
                    if (results[0]) {
                        locationInput.value = results[0].formatted_address;
                    }
                }
            });
        });

        // Try to get user's location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const pos = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    };
                    map.setCenter(pos);
                    marker.setPosition(pos);

                    // Get address for the location
                    geocoder.geocode({ location: pos }, (results, status) => {
                        if (status === 'OK') {
                            if (results[0]) {
                                locationInput.value = results[0].formatted_address;
                            }
                        }
                    });
                }
            );
        }
    } else {
        // We're on the view card page
        const location = document.querySelector('.contact-info p:last-child').textContent;
        geocoder.geocode({ address: location }, (results, status) => {
            if (status === 'OK') {
                const position = results[0].geometry.location;
                map.setCenter(position);
                new google.maps.Marker({
                    map: map,
                    position: position
                });
            }
        });
    }
}