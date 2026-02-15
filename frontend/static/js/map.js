// frontend/static/js/map.js - LIFEXIA Health Grid Map Integration
// Matches the Health Grid "Verified Infrastructure" design

let map = null;
let currentCategory = 'ALL RESOURCES';
let nearbyLocations = [];
let mapResizeObserver = null;
let markers = [];
let userMarker = null;
let routeLine = null;
let selectedLocation = null;
let userLocation = null;

const MAP_API_BASE = window.API_BASE || '/api';

// ──────────────── Map Modal Controls ────────────────

async function showMapModal() {
    const modal = document.getElementById('mapModal');
    if (!modal) return;

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    // Try to detect user location first
    detectUserLocation();

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
    document.body.style.overflow = '';

    if (mapResizeObserver) {
        mapResizeObserver.disconnect();
        mapResizeObserver = null;
    }

    if (map) {
        map.remove();
        map = null;
    }
    markers = [];
    userMarker = null;
    routeLine = null;
}

function detectUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
            },
            () => {
                // Default: Ahmedabad center
                userLocation = { lat: 23.0225, lng: 72.5714 };
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    }
}

// ──────────────── API Integration ────────────────

async function fetchLocationsFromBackend() {
    const statusEl = document.getElementById('locationCount');
    if (statusEl) statusEl.textContent = 'Scanning nodes...';

    try {
        const params = new URLSearchParams();

        if (userLocation) {
            params.append('lat', userLocation.lat);
            params.append('lng', userLocation.lng);
        }

        if (currentCategory !== 'ALL RESOURCES') {
            params.append('category', currentCategory);
        }

        const response = await fetch(`${MAP_API_BASE}/map/locations?${params.toString()}`);

        if (response.ok) {
            const data = await response.json();
            nearbyLocations = data.locations || [];
            if (statusEl) {
                statusEl.textContent = `${nearbyLocations.length} nearby nodes`;
            }
        } else {
            nearbyLocations = [];
            if (statusEl) statusEl.textContent = 'Error loading nodes';
        }
    } catch (error) {
        console.error('Error fetching locations:', error);
        nearbyLocations = [];
        if (statusEl) statusEl.textContent = 'Connection error';
    }
}

async function searchLocations(query) {
    if (!query || query.length < 2) return;

    try {
        const params = new URLSearchParams({ q: query });
        if (userLocation) {
            params.append('lat', userLocation.lat);
            params.append('lng', userLocation.lng);
        }

        const response = await fetch(`${MAP_API_BASE}/map/search?${params.toString()}`);

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
    return nearbyLocations;
}

// ──────────────── Sidebar Location List ────────────────

function renderLocationsList() {
    const locationsList = document.getElementById('locationsList');
    if (!locationsList) return;

    const filtered = getFilteredLocations();
    const statusEl = document.getElementById('locationCount');

    if (statusEl) {
        statusEl.textContent = `${filtered.length} nearby nodes`;
    }

    if (filtered.length === 0) {
        locationsList.innerHTML = `
            <div class="text-center py-12 px-4">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                    <svg class="w-8 h-8 text-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <p class="text-white/40 text-xs uppercase tracking-widest font-bold">No nodes found</p>
                <p class="text-white/25 text-[10px] mt-1">Try adjusting your filters</p>
            </div>
        `;
        return;
    }

    locationsList.innerHTML = filtered.map((loc, idx) => {
        const isSelected = selectedLocation?.id === loc.id;
        const typeColor = getTypeColor(loc.type);
        const isHospital = (loc.type || '').toUpperCase() === 'HOSPITAL';

        return `
        <div class="health-grid-card ${isSelected ? 'health-grid-card-active' : ''}" 
             onclick="focusLocation(${idx})" 
             data-location-id="${loc.id}">
            
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0 mt-0.5">
                    <div class="w-8 h-8 rounded-lg ${typeColor.bg} flex items-center justify-center">
                        ${isHospital ? 
                            `<svg class="w-4 h-4 ${typeColor.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                            </svg>` :
                            `<svg class="w-4 h-4 ${typeColor.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                            </svg>`
                        }
                    </div>
                </div>
                
                <div class="flex-1 min-w-0">
                    <h3 class="text-white font-semibold text-sm leading-tight truncate">${loc.name}</h3>
                    <p class="text-[10px] uppercase tracking-widest font-bold mt-1 ${typeColor.label}">
                        ${loc.type || 'HOSPITAL'}
                    </p>
                </div>

                ${loc.distance != null ? `
                    <div class="text-right flex-shrink-0">
                        <span class="text-white/90 text-xs font-bold block">${loc.distance} km</span>
                        <span class="text-white/50 text-[10px]">${loc.estimatedTime || '~'} min</span>
                    </div>
                ` : ''}
            </div>

            ${(loc.ayushmanCard || loc.maaCard || loc.speciality) ? `
                <div class="flex items-center gap-2 mt-2.5 flex-wrap">
                    ${loc.ayushmanCard ? '<span class="health-badge health-badge-ayushman">Ayushman</span>' : ''}
                    ${loc.maaCard ? '<span class="health-badge health-badge-maa">MAA Card</span>' : ''}
                    ${loc.speciality ? `<span class="health-badge health-badge-spec">${loc.speciality}</span>` : ''}
                    ${loc.open24x7 ? '<span class="health-badge health-badge-open">24/7</span>' : ''}
                </div>
            ` : ''}

            <div class="flex gap-2 mt-3">
                <button onclick="event.stopPropagation(); getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" 
                        class="health-grid-btn flex-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path>
                    </svg>
                    Directions
                </button>
                ${loc.contact ? `
                    <button onclick="event.stopPropagation(); window.open('tel:${loc.contact}', '_blank')" 
                            class="health-grid-btn flex-1 health-grid-btn-call">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path>
                        </svg>
                        Call
                    </button>
                ` : ''}
                <button onclick="event.stopPropagation(); shareOnWhatsApp(${idx})" 
                        class="health-grid-btn health-grid-btn-wa" title="Share via WhatsApp">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                    </svg>
                </button>
            </div>
        </div>
        `;
    }).join('');
}

function getTypeColor(type) {
    const t = (type || '').toUpperCase();
    if (t === 'PHARMACY') {
        return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'text-emerald-400/80' };
    }
    return { bg: 'bg-red-500/20', text: 'text-red-400', label: 'text-red-400/80' };
}

// ──────────────── Leaflet Map ────────────────

function initializeMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;

    if (map) map.remove();
    mapDiv.innerHTML = '';

    const defaultCenter = userLocation ? [userLocation.lat, userLocation.lng] : [23.0225, 72.5714];

    map = L.map('map', {
        center: defaultCenter,
        zoom: 13,
        zoomControl: false
    });

    // Use standard tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
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

                // Custom user marker with pulsing effect
                const userIcon = L.divIcon({
                    html: `
                        <div class="user-marker-container">
                            <div class="user-marker-pulse"></div>
                            <div class="user-marker-dot">
                                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                </svg>
                            </div>
                        </div>
                    `,
                    className: '',
                    iconSize: [48, 48],
                    iconAnchor: [24, 24]
                });

                userMarker = L.marker(userPos, { icon: userIcon }).addTo(map);
                userMarker.bindPopup(`
                    <div class="map-popup-content">
                        <p class="font-bold text-sm mb-1">Your Location</p>
                        <p class="text-xs text-gray-500">Current GPS position</p>
                    </div>
                `);

                // Re-fetch with location
                fetchLocationsFromBackend().then(() => {
                    renderLocationsList();
                    updateMapMarkers();
                });
            },
            () => {
                console.log('Geolocation denied, using default center');
            }
        );
    }

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

    markers.forEach(marker => marker.remove());
    markers = [];

    if (routeLine) {
        routeLine.remove();
        routeLine = null;
    }

    const filtered = getFilteredLocations();

    filtered.forEach((loc, idx) => {
        const isHospital = (loc.type || '').toUpperCase() === 'HOSPITAL';
        const markerColor = isHospital ? '#ef4444' : '#10b981';
        const markerBg = isHospital ? 'bg-red-500' : 'bg-emerald-500';

        const icon = L.divIcon({
            html: `
                <div class="map-marker-pin ${markerBg}">
                    <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        ${isHospital ?
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>' :
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>'
                        }
                    </svg>
                    <div class="map-marker-arrow" style="border-top-color: ${markerColor}"></div>
                </div>
            `,
            className: '',
            iconSize: [36, 44],
            iconAnchor: [18, 44],
            popupAnchor: [0, -44]
        });

        const marker = L.marker([loc.lat, loc.lng], { icon: icon }).addTo(map);

        // Popup content
        const popupContent = `
            <div class="map-popup-content">
                <div class="flex items-start justify-between mb-2">
                    <h3 class="font-bold text-sm text-gray-900 pr-2 leading-tight">${loc.name}</h3>
                    <div class="flex gap-1 flex-shrink-0">
                        ${loc.ayushmanCard ? '<span class="inline-block text-[8px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded-full font-bold">PMJAY</span>' : ''}
                        ${loc.maaCard ? '<span class="inline-block text-[8px] px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full font-bold">MAA</span>' : ''}
                    </div>
                </div>
                
                <p class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-2">${loc.type || 'Hospital'} ${loc.speciality ? '- ' + loc.speciality : ''}</p>
                
                ${loc.distance != null ? `
                    <div class="flex items-center gap-3 mb-2 text-xs text-gray-600">
                        <span class="flex items-center gap-1"><span class="text-red-500">&#9679;</span> ${loc.distance} km</span>
                        <span class="flex items-center gap-1"><span class="text-blue-500">&#9679;</span> ${loc.estimatedTime} min</span>
                    </div>
                ` : ''}
                
                ${loc.benefit ? `<p class="text-xs text-gray-600 mb-3 leading-relaxed">${loc.benefit.substring(0, 120)}${loc.benefit.length > 120 ? '...' : ''}</p>` : ''}
                
                <div class="flex gap-2">
                    <button onclick="getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" 
                            class="flex-1 text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg font-semibold transition-colors flex items-center justify-center gap-1">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path></svg>
                        Directions
                    </button>
                    ${loc.contact ? `
                        <button onclick="window.open('tel:${loc.contact}', '_blank')" 
                                class="flex-1 text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg font-semibold transition-colors flex items-center justify-center gap-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>
                            Call
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        marker.bindPopup(popupContent, { maxWidth: 300, minWidth: 240 });

        marker.on('click', () => {
            selectedLocation = loc;
            highlightLocation(loc.id);
            if (userMarker) {
                drawRoute(userMarker.getLatLng(), marker.getLatLng());
            }
        });

        markers.push(marker);
    });
}

// ──────────────── Interactions ────────────────

function focusLocation(index) {
    const filtered = getFilteredLocations();
    const loc = filtered[index];

    if (!loc || !map) return;

    selectedLocation = loc;
    highlightLocation(loc.id);

    map.setView([loc.lat, loc.lng], 15);

    const markerIndex = filtered.findIndex(l => l.id === loc.id);
    if (markerIndex >= 0 && markers[markerIndex]) {
        markers[markerIndex].openPopup();
        if (userMarker) {
            drawRoute(userMarker.getLatLng(), markers[markerIndex].getLatLng());
        }
    }
}

function highlightLocation(locationId) {
    document.querySelectorAll('[data-location-id]').forEach(el => {
        el.classList.remove('health-grid-card-active');
    });

    const locationEl = document.querySelector(`[data-location-id="${locationId}"]`);
    if (locationEl) {
        locationEl.classList.add('health-grid-card-active');
        locationEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function drawRoute(from, to) {
    if (routeLine) routeLine.remove();

    routeLine = L.polyline([from, to], {
        color: '#3b82f6',
        weight: 3,
        opacity: 0.8,
        dashArray: '8, 8'
    }).addTo(map);

    map.fitBounds(routeLine.getBounds(), { padding: [60, 60] });
}

function getDirections(event, lat, lng, name) {
    if (event) event.stopPropagation();
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
    window.open(url, '_blank');
}

function shareOnWhatsApp(index) {
    const filtered = getFilteredLocations();
    const loc = filtered[index];
    if (!loc) return;

    const mapsLink = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`;
    const message = encodeURIComponent(
        `*${loc.name}*\n` +
        `Type: ${loc.type || 'Hospital'}\n` +
        (loc.speciality ? `Specialty: ${loc.speciality}\n` : '') +
        (loc.contact ? `Contact: ${loc.contact}\n` : '') +
        (loc.address ? `Address: ${loc.address}\n` : '') +
        (loc.ayushmanCard ? '* Ayushman Card Accepted\n' : '') +
        (loc.maaCard ? '* MAA Card Accepted\n' : '') +
        `\nDirections: ${mapsLink}\n\n` +
        `Shared via LIFEXIA Health Grid`
    );
    window.open(`https://wa.me/?text=${message}`, '_blank');
}

async function refreshSearch() {
    if (typeof showLoading === 'function') showLoading();

    await fetchLocationsFromBackend();
    renderLocationsList();
    updateMapMarkers();

    if (typeof hideLoading === 'function') hideLoading();
    if (typeof showNotification === 'function') {
        showNotification('Health Grid refreshed', 'success');
    }
}

// ──────────────── Custom Map Styles ────────────────

if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        /* Map tiles - slight desaturation for dark theme contrast */
        .map-tiles {
            filter: brightness(0.95) contrast(1.05) saturate(0.9);
        }

        /* Custom map marker pin */
        .map-marker-pin {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 36px;
            height: 36px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 2.5px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }
        .map-marker-pin:hover {
            transform: rotate(-45deg) scale(1.15);
        }
        .map-marker-pin svg {
            transform: rotate(45deg);
        }
        .map-marker-arrow {
            display: none;
        }

        /* User location marker */
        .user-marker-container {
            position: relative;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .user-marker-pulse {
            position: absolute;
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.3);
            animation: userPulse 2s ease-in-out infinite;
        }
        .user-marker-dot {
            position: relative;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            border: 3px solid white;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2;
        }

        @keyframes userPulse {
            0%, 100% { transform: scale(0.8); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0; }
        }

        /* Leaflet popup styling */
        .leaflet-popup-content-wrapper {
            background: rgba(255, 255, 255, 0.98) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2) !important;
            padding: 0 !important;
        }
        .leaflet-popup-content {
            margin: 0 !important;
            line-height: 1.5 !important;
        }
        .map-popup-content {
            padding: 16px;
            min-width: 240px;
        }
        .leaflet-popup-tip {
            background: rgba(255, 255, 255, 0.98) !important;
        }
        .leaflet-popup-close-button {
            color: #6b7280 !important;
            font-size: 20px !important;
            padding: 4px 8px !important;
        }
        .leaflet-container {
            font-family: inherit;
        }
        
        /* Zoom control styling */
        .leaflet-control-zoom {
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            border-radius: 12px !important;
            overflow: hidden;
        }
        .leaflet-control-zoom a {
            background: rgba(255,255,255,0.95) !important;
            color: #374151 !important;
            border-bottom: 1px solid rgba(0,0,0,0.1) !important;
        }
    `;
    document.head.appendChild(style);
}
