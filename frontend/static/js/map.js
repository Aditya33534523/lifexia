// frontend/static/js/map.js - Mappls Map Integration with Filtering

let map = null;
let currentCategory = 'All';
let nearbyLocations = []; // Will be populated from JSON
let mapResizeObserver = null;
let markers = [];

// Categories to support
const categories = ['All', 'Hospital', 'Pharmacy', 'Gynecologist', 'Orthopedic', 'Pediatrician', 'General Physician'];

async function showMapModal() {
    document.getElementById('mapModal').classList.remove('hidden');
    document.getElementById('mapCategoryFilter').value = currentCategory;

    // Fetch data if not already loaded
    if (nearbyLocations.length === 0) {
        await fetchLocations();
    } else {
        renderLocations();
    }

    // Initialize map after a short delay to ensure container is visible
    setTimeout(() => {
        initializeMap();
    }, 500); // Increased delay for better stability
}

function closeMapModal() {
    document.getElementById('mapModal').classList.add('hidden');
    if (mapResizeObserver) {
        mapResizeObserver.disconnect();
        mapResizeObserver = null;
    }
    // Mappls map instance cleanup if needed
    map = null;
}

async function fetchLocations() {
    const statusEl = document.getElementById('locationCount');
    if (statusEl) statusEl.textContent = 'Loading locations...';

    try {
        const response = await fetch('/static/js/locations.json');
        if (!response.ok) throw new Error('Failed to load locations');
        nearbyLocations = await response.json();
        renderLocations();
    } catch (error) {
        console.error('Error loading locations:', error);
        if (statusEl) statusEl.textContent = 'Error loading data.';
    }
}

function filterMapCategory(category) {
    currentCategory = category;
    renderLocations();
    initializeMap(); // Re-render markers and map
}

function getFilteredLocations() {
    if (currentCategory === 'All') {
        return nearbyLocations;
    }
    return nearbyLocations.filter(loc => {
        return (loc.category === currentCategory) || (loc.type && loc.type.includes(currentCategory));
    });
}

function renderLocations() {
    const locationsList = document.getElementById('locationsList');
    const filtered = getFilteredLocations();
    const statusEl = document.getElementById('locationCount');

    if (statusEl) {
        statusEl.textContent = `${filtered.length} locations found`;
    }

    if (filtered.length === 0) {
        locationsList.innerHTML = '<div class="text-white/60 text-center py-4">No locations found.</div>';
        return;
    }

    locationsList.innerHTML = filtered.map((loc, idx) => `
        <div class="glassmorphism-strong rounded-xl p-4 hover:bg-white/30 transition-all cursor-pointer group" onclick="focusLocation(${idx})">
            <div class="flex items-start justify-between mb-2">
                <div class="flex-1">
                    <h3 class="text-white font-semibold group-hover:text-blue-300 transition-colors">${loc.name}</h3>
                    <p class="text-white/70 text-xs uppercase tracking-wider">${loc.type}</p>
                </div>
                ${loc.distance ? `<span class="text-white/80 text-xs glassmorphism px-2 py-1 rounded-lg font-medium whitespace-nowrap">${loc.distance}</span>` : ''}
            </div>
            
            <div class="space-y-1">
                 ${loc.address ? `
                    <div class="flex items-start text-white/60 text-xs">
                        <svg class="w-3 h-3 mr-1.5 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        </svg>
                        <span class="line-clamp-2">${loc.address}</span>
                    </div>
                ` : ''}
            </div>
            
            <div class="mt-3 flex gap-2">
                 <button onclick="getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" class="flex-1 text-xs text-white/90 hover:text-white flex items-center justify-center gap-1 glassmorphism p-1.5 rounded-lg hover:bg-blue-500/30 transition-all">
                    Directions
                </button>
            </div>
        </div>
    `).join('');
}

function initializeMap() {
    const mapDiv = document.getElementById('map');
    if (!mapDiv) return;
    mapDiv.innerHTML = ''; // Clear previous map content

    console.log("Initializing Mappls Map...");
    if (typeof mappls === 'undefined') {
        console.error("Mappls SDK not loaded!");
        mapDiv.innerHTML = '<div class="text-white p-4">Error: Map SDK not loaded. Please check your internet connection or API key.</div>';
        return;
    }

    // Create Mappls Map
    map = new mappls.Map('map', {
        center: [23.0225, 72.5714], // Ahmedabad
        zoom: 12,
        hybrid: true
    });

    map.on('load', () => {
        console.log("Mappls Map loaded successfully.");
        const filtered = getFilteredLocations();
        markers = [];
        const bounds = new mappls.LatLngBounds();

        filtered.forEach((loc, idx) => {
            const latlng = { lat: loc.lat, lng: loc.lng };

            const markerOptions = {
                map: map,
                position: latlng,
                title: loc.name,
                html: `
                    <div style="min-width: 200px; padding: 10px;">
                        <h3 style="font-weight: bold; color: #1f2937;">${loc.name}</h3>
                        <p style="color: #6b7280; font-size: 13px;">${loc.type}</p>
                        <button onclick="getDirections(event, ${loc.lat}, ${loc.lng}, '${loc.name.replace(/'/g, "\\'")}')" 
                                style="background: #1e40af; color: white; border: none; padding: 5px; width: 100%; border-radius: 4px; margin-top: 5px; cursor: pointer;">
                            Get Directions
                        </button>
                    </div>
                `
            };

            // Custom icon for Hospitals
            if (loc.category === 'Hospital' || loc.type === 'Hospital') {
                markerOptions.icon = '/static/images/hospital-pin.png';
                markerOptions.width = 40;
                markerOptions.height = 40;
            }

            const marker = new mappls.Marker(markerOptions);
            markers.push(marker);
            bounds.extend(latlng);
        });

        if (markers.length > 0) {
            map.fitBounds(bounds);
        }
    });

    // Resize Handling
    if (mapResizeObserver) mapResizeObserver.disconnect();
    mapResizeObserver = new ResizeObserver(() => {
        if (map && map.resize) map.resize();
    });
    mapResizeObserver.observe(mapDiv);
}

function focusLocation(index) {
    const filtered = getFilteredLocations();
    const loc = filtered[index];

    if (map && loc && markers[index]) {
        map.setCenter({ lat: loc.lat, lng: loc.lng });
        map.setZoom(16);
        // Mappls has its own way to open info window, often via marker title or custom logic
        // For simplicity, we center the map.
    }
}

function getDirections(event, lat, lng, name) {
    if (event) event.stopPropagation();
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
    window.open(url, '_blank');
}

