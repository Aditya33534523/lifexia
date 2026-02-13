// frontend/static/js/map.js - Enhanced Map Integration with Backend API

let map = null;
let currentCategory = 'ALL RESOURCES';
let nearbyLocations = [];
let mapResizeObserver = null;
let markers = [];
let userMarker = null;
let routeLine = null;
let selectedLocation = null;
let userLocation = null;

// API Base URL
const API_BASE = window.API_BASE || '/api';

async function showMapModal() {
    const modal = document.getElementById('mapModal');
    if (!modal) return;

    modal.classList.remove('hidden');

    // Fetch data from backend
    await fetchLocationsFromBackend();

    // Initialize map after modal is visible
    setTimeout(() => {
        initializeMap();
        renderLocationsList();
    }, 300);
}

function closeMapModal() {
    const modal = document.getElementById('mapModal');
    if (modal) {
        modal.classList.add('hidden');
    }

    if (mapResizeObserver) {
        mapResizeObserver.disconnect();
        mapResizeObserver = null;
    }

    // Cleanup map
    if (map) {
        map.remove();
        map = null;
    }
    markers = [];
    userMarker = null;
    routeLine = null;
}

async function fetchLocationsFromBackend() {
    const statusEl = document.getElementById('locationCount');
    if (statusEl) statusEl.textContent = 'Loading locations...';

    try {
        // Build query parameters
        const params = new URLSearchParams();

        // Add user location if available
        if (userLocation) {
            params.append('lat', userLocation.lat);
            params.append('lng', userLocation.lng);
        }

        // Add category filter if not "ALL RESOURCES"
        if (currentCategory !== 'ALL RESOURCES') {
            params.append('category', currentCategory);
        }

        const response = await fetch(`${API_BASE}/map/locations?${params.toString()}`);

        if (response.ok) {
            const data = await response.json();
            nearbyLocations = data.locations || [];

            if (statusEl) {
                statusEl.textContent = `${nearbyLocations.length} locations`;
            }
        } else {
            console.error('Failed to fetch locations from backend');
            // Fallback to empty array
            nearbyLocations = [];
            if (statusEl) {
                statusEl.textContent = 'Error loading locations';
            }
        }
    } catch (error) {
        console.error('Error fetching locations:', error);
        nearbyLocations = [];
        if (statusEl) {
            statusEl.textContent = 'Connection error';
        }
    }
}

async function searchLocations(query) {
    if (!query || query.length < 2) return;

    try {
        const params = new URLSearchParams({
            q: query
        });

        if (userLocation) {
            params.append('lat', userLocation.lat);
            params.append('lng', userLocation.lng);
        }

        const response = await fetch(`${API_BASE}/map/search?${params.toString()}`);

        if (response.ok) {
            const data = await response.json();
            nearbyLocations = data.results || [];
            renderLocationsList();
            updateMapMarkers();
        }
    } catch (error) {
        console.error('Search error:', error);
    }
}

async function filterMapCategory(category) {
    currentCategory = category;
    await fetchLocationsFromBackend();
    renderLocationsList();
    updateMapMarkers();
}

function getFilteredLocations() {
    // Backend already handles filtering, so just return all locations
    return nearbyLocations;
}

function renderLocationsList() {
    const locationsList = document.getElementById('locationsList');
    if (!locationsList) return;

    const filtered = getFilteredLocations();
    const statusEl = document.getElementById('locationCount');

    if (statusEl) {
        statusEl.textContent = `${filtered.length} locations`;
    }

    if (filtered.length === 0) {
        locationsList.innerHTML = `
            <div class="text-white/60 text-center py-8">
                <svg class="w-12 h-12 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <p class="text-xs uppercase tracking-wider">No locations found</p>
            </div>
        `;
        return;
    }

    locationsList.innerHTML = filtered.map((loc, idx) => `
        <div class="glassmorphism-strong rounded-xl p-4 hover:bg-white/20 transition-all cursor-pointer group ${selectedLocation?.id === loc.id ? 'ring-2 ring-blue-400' : ''}" 
             onclick="focusLocation(${idx})" 
             data-location-id="${loc.id}">
            <div class="flex items-start justify-between mb-2">
                <div class="flex-1 min-w-0">
                    <h3 class="text-white font-semibold text-sm group-hover:text-blue-300 transition-colors truncate">
                        ${loc.name}
                    </h3>
                    <p class="text-white/70 text-[10px] uppercase tracking-wider font-bold mt-1">
                        ${loc.type || 'HOSPITAL'}
                    </p>
                </div>
                ${loc.distance ? `
                    <div class="ml-2 text-right">
                        <span class="text-white/90 text-xs font-bold block">${loc.distance} km</span>
                        <span class="text-white/60 text-[10px]">${loc.estimatedTime || '~'} min</span>
                    </div>
                ` : ''}
            </div>
            
            <div class="flex items-center gap-1.5 mb-2">
                ${loc.ayushmanCard || loc.maaCard ? `
                    <div class="flex gap-1">
                        ${loc.ayushmanCard ? '<div class="w-2 h-2 rounded-full bg-emerald-500" title="Ayushman Card"></div>' : ''}
                        ${loc.maaCard ? '<div class="w-2 h-2 rounded-full bg-purple-500" title="Maa Amrutam"></div>' : ''}
                    </div>
                ` : ''}
                ${loc.speciality ? `
                    <span class="text-[10px] px-2 py-1 bg-blue-500/20 text-blue-400 rounded-lg font-bold uppercase tracking-wider">
                        ${loc.speciality}
                    </span>
                ` : ''}
            </div>
            
            ${loc.benefit ? `
                <p class="text-white/60 text-xs mb-3 line-clamp-2">${loc.benefit}</p>
            ` : ''}
            
            <div class="flex gap-2">
                <button onclick="event.stopPropagation(); getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" 
                        class="flex-1 text-[10px] text-white/90 hover:text-white flex items-center justify-center gap-1 glassmorphism p-2 rounded-lg hover:bg-blue-500/30 transition-all font-bold uppercase tracking-wider">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path>
                    </svg>
                    Route
                </button>
                ${loc.contact ? `
                    <button onclick="event.stopPropagation(); window.open('tel:${loc.contact}', '_blank')" 
                            class="flex-1 text-[10px] text-white/90 hover:text-white flex items-center justify-center gap-1 glassmorphism p-2 rounded-lg hover:bg-green-500/30 transition-all font-bold uppercase tracking-wider">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                        </svg>
                        Call
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function initializeMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;

    // Clear existing map
    if (map) {
        map.remove();
    }

    mapDiv.innerHTML = '';

    // Default center (Ahmedabad)
    const defaultCenter = [23.0225, 72.5714];

    // Initialize Leaflet map
    map = L.map('map', {
        center: defaultCenter,
        zoom: 12,
        zoomControl: true
    });

    // Add tile layer with dark theme
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        className: 'map-tiles'
    }).addTo(map);

    // Try to get user location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userPos = [position.coords.latitude, position.coords.longitude];
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                map.setView(userPos, 13);

                // Add user marker
                const userIcon = L.divIcon({
                    html: `
                        <div class="relative flex items-center justify-center w-12 h-12 bg-blue-500/90 border-2 border-white rounded-full shadow-lg">
                            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                        </div>
                    `,
                    className: '',
                    iconSize: [48, 48],
                    iconAnchor: [24, 24]
                });

                userMarker = L.marker(userPos, { icon: userIcon }).addTo(map);
                userMarker.bindPopup(`
                    <div class="p-2 min-w-[150px]">
                        <p class="font-bold text-sm mb-1">Your Location</p>
                        <p class="text-xs text-gray-600">Current position</p>
                    </div>
                `);

                // Fetch locations with user coordinates
                fetchLocationsFromBackend();
            },
            (error) => {
                console.log('Geolocation error:', error);
            }
        );
    }

    // Add location markers
    updateMapMarkers();

    // Handle map resize
    if (mapResizeObserver) mapResizeObserver.disconnect();
    mapResizeObserver = new ResizeObserver(() => {
        if (map) map.invalidateSize();
    });
    mapResizeObserver.observe(mapDiv);
}

function updateMapMarkers() {
    if (!map) return;

    // Clear existing markers (except user marker)
    markers.forEach(marker => marker.remove());
    markers = [];

    if (routeLine) {
        routeLine.remove();
        routeLine = null;
    }

    const filtered = getFilteredLocations();

    filtered.forEach((loc, idx) => {
        const icon = L.divIcon({
            html: `
                <div class="relative flex items-center justify-center w-10 h-10 bg-red-500/90 border-2 border-white rounded-full shadow-lg hover:scale-110 transition-transform">
                    <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                    </svg>
                </div>
            `,
            className: '',
            iconSize: [40, 40],
            iconAnchor: [20, 20],
            popupAnchor: [0, -20]
        });

        const marker = L.marker([loc.lat, loc.lng], { icon: icon }).addTo(map);

        // Create popup content
        const popupContent = `
            <div class="p-3 min-w-[250px]">
                <div class="flex items-start justify-between mb-2">
                    <h3 class="font-bold text-sm pr-2">${loc.name}</h3>
                    ${loc.ayushmanCard || loc.maaCard ? `
                        <div class="flex gap-1">
                            ${loc.ayushmanCard ? '<span class="text-[8px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-600 rounded font-bold">A</span>' : ''}
                            ${loc.maaCard ? '<span class="text-[8px] px-1.5 py-0.5 bg-purple-500/20 text-purple-600 rounded font-bold">M</span>' : ''}
                        </div>
                    ` : ''}
                </div>
                
                <p class="text-xs text-gray-600 font-semibold uppercase mb-2">${loc.type || 'Hospital'}</p>
                
                ${loc.distance ? `
                    <div class="flex items-center gap-3 mb-2 text-xs text-gray-700">
                        <span>📍 ${loc.distance} km</span>
                        <span>⏱️ ${loc.estimatedTime} min</span>
                    </div>
                ` : ''}
                
                ${loc.speciality ? `
                    <span class="inline-block text-[10px] px-2 py-1 bg-blue-500/20 text-blue-600 rounded font-bold uppercase mb-2">
                        ${loc.speciality}
                    </span>
                ` : ''}
                
                ${loc.benefit ? `
                    <p class="text-xs text-gray-700 mb-3 leading-relaxed">${loc.benefit}</p>
                ` : ''}
                
                <div class="flex gap-2">
                    <button onclick="getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" 
                            class="flex-1 text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg font-semibold transition-colors">
                        Get Directions
                    </button>
                    ${loc.contact ? `
                        <button onclick="window.open('tel:${loc.contact}', '_blank')" 
                                class="flex-1 text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg font-semibold transition-colors">
                            Call
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        marker.bindPopup(popupContent);

        marker.on('click', () => {
            selectedLocation = loc;
            highlightLocation(loc.id);

            // Draw route if user location is available
            if (userMarker) {
                drawRoute(userMarker.getLatLng(), marker.getLatLng());
            }
        });

        markers.push(marker);
    });
}

function focusLocation(index) {
    const filtered = getFilteredLocations();
    const loc = filtered[index];

    if (!loc || !map) return;

    selectedLocation = loc;
    highlightLocation(loc.id);

    // Center map on location
    map.setView([loc.lat, loc.lng], 15);

    // Open popup for the corresponding marker
    const markerIndex = filtered.findIndex(l => l.id === loc.id);
    if (markerIndex >= 0 && markers[markerIndex]) {
        markers[markerIndex].openPopup();

        // Draw route if user location is available
        if (userMarker) {
            drawRoute(userMarker.getLatLng(), markers[markerIndex].getLatLng());
        }
    }
}

function highlightLocation(locationId) {
    // Remove previous highlights
    document.querySelectorAll('[data-location-id]').forEach(el => {
        el.classList.remove('ring-2', 'ring-blue-400');
    });

    // Add highlight to selected location
    const locationEl = document.querySelector(`[data-location-id="${locationId}"]`);
    if (locationEl) {
        locationEl.classList.add('ring-2', 'ring-blue-400');
        // Scroll into view
        locationEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function drawRoute(from, to) {
    if (routeLine) {
        routeLine.remove();
    }

    routeLine = L.polyline([from, to], {
        color: '#3b82f6',
        weight: 3,
        opacity: 0.7,
        dashArray: '10, 10'
    }).addTo(map);

    // Fit map to show both points
    map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

function getDirections(event, lat, lng, name) {
    if (event) event.stopPropagation();
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
    window.open(url, '_blank');
}

async function refreshSearch() {
    if (typeof showLoading === 'function') showLoading();

    await fetchLocationsFromBackend();
    renderLocationsList();
    updateMapMarkers();

    if (typeof hideLoading === 'function') hideLoading();
    if (typeof showNotification === 'function') {
        showNotification('Locations refreshed', 'success');
    }
}

// Add custom styles for the map
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        .map-tiles {
            filter: brightness(0.9) contrast(1.1);
        }
        
        .leaflet-popup-content-wrapper {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }
        
        .leaflet-popup-tip {
            background: rgba(255, 255, 255, 0.98);
        }
        
        .leaflet-container {
            font-family: inherit;
        }
    `;
    document.head.appendChild(style);
}