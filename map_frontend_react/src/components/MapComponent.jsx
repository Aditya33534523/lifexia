import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Navigation, Phone, Clock, Star } from 'lucide-react';

// Fix for default Leaflet icon paths in React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [0, -35]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom Hospital Icon
const hospitalIcon = L.icon({
    iconUrl: '/hospital-pin.png',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
});

// Custom Pharmacy Icon
const pharmacyIcon = L.icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjMTBiOTgxIj48cGF0aCBkPSJNMTkgM2gtNC4xOEMxNC40IDEuODQgMTMuMyAxIDEyIDFzLTIuNCAuODQtMi44MiAySDVjLTEuMSAwLTIgLjktMiAydjE0YzAgMS4xLjkgMiAyIDJoMTRjMS4xIDAgMi0uOSAyLTJWNWMwLTEuMS0uOS0yLTItMnptLTcgMGMuNTUgMCAxIC40NSAxIDFzLS40NSAxLTEgMS0xLS40NS0xLTEgLjQ1LTEgMS0xem0wIDE2Yy0zLjMxIDAtNi0yLjY5LTYtNnMyLjY5LTYgNi02IDYgMi42OSA2IDYtMi42OSA2LTYgNnoiLz48cGF0aCBkPSJNMTMuNSAxMC41aC0zaC0xdjNoMXYzaDN2LTNoMXYtM3oiLz48L3N2Zz4=',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
});

// Gynecologist Icon
const gyneIcon = L.icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjZWM0ODk5Ij48cGF0aCBkPSJNMTIgMkM2LjQ4IDIgMiA2LjQ4IDIgMTJzNC40OCAxMCAxMCAxMCAxMC00LjQ4IDEwLTEwUzE3LjUyIDIgMTIgMnptMCAxOGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6bTAtMTRjLTIuMjEgMC00IDEuNzktNCA0czEuNzkgNCA0IDQgNC0xLjc5IDQtNC0xLjc5LTQtNC00eiIvPjwvc3ZnPg==',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
});

// User location icon
const userIcon = L.icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMCIgaGVpZ2h0PSIzMCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjMzMzMyNmZiI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0iIzMzMzNmZiIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiLz48L3N2Zz4=',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -10]
});

// Get icon based on category
function getIconForCategory(category) {
    const cat = category?.toLowerCase() || '';
    if (cat.includes('hospital')) return hospitalIcon;
    if (cat.includes('pharmacy') || cat.includes('medical')) return pharmacyIcon;
    if (cat.includes('gynec') || cat.includes('maternity')) return gyneIcon;
    return DefaultIcon;
}

// Helper component to handle focusing/centering
function MapController({ focusLocation, userLocation, locations, showDirections }) {
    const map = useMap();

    useEffect(() => {
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }, [map]);

    useEffect(() => {
        if (focusLocation) {
            map.setView([focusLocation.lat, focusLocation.lng], 16, {
                animate: true,
                duration: 1
            });
        } else if (userLocation) {
            // Fit bounds to show user and nearby locations
            const bounds = L.latLngBounds([
                [userLocation.lat, userLocation.lng]
            ]);
            
            locations.slice(0, 5).forEach(loc => {
                bounds.extend([loc.lat, loc.lng]);
            });
            
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [focusLocation, userLocation, map, locations]);

    return null;
}

// Component to show user location
function UserLocation({ position }) {
    if (!position) return null;
    
    return (
        <>
            <Circle
                center={[position.lat, position.lng]}
                radius={100}
                pathOptions={{
                    fillColor: '#3333ff',
                    fillOpacity: 0.2,
                    color: '#3333ff',
                    weight: 2
                }}
            />
            <Marker position={[position.lat, position.lng]} icon={userIcon}>
                <Popup>
                    <div className="p-1 min-w-[120px]">
                        <h3 className="font-bold text-blue-600">Your Location</h3>
                        <p className="text-xs text-gray-500 mt-1">Accuracy: ±100m</p>
                    </div>
                </Popup>
            </Marker>
        </>
    );
}

function MapComponent({ locations, focusLocation }) {
    const defaultCenter = [23.0225, 72.5714]; // Ahmedabad
    const [userLocation, setUserLocation] = useState(null);
    const [loadingLocation, setLoadingLocation] = useState(false);

    const getUserLocation = () => {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        setLoadingLocation(true);
        navigator.geolocation.getCurrentPosition(
            (position) => {
                setUserLocation({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
                setLoadingLocation(false);
            },
            (error) => {
                console.error('Error getting location:', error);
                alert('Unable to get your location. Please enable location access.');
                setLoadingLocation(false);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    };

    const getDirections = (loc) => {
        if (userLocation) {
            const url = `https://www.google.com/maps/dir/${userLocation.lat},${userLocation.lng}/${loc.lat},${loc.lng}`;
            window.open(url, '_blank');
        } else {
            const url = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`;
            window.open(url, '_blank');
        }
    };

    return (
        <div className="relative h-full w-full" style={{ height: '100vh', width: '100%' }}>
            {/* Location Button */}
            <button
                onClick={getUserLocation}
                disabled={loadingLocation}
                className="absolute top-4 right-4 z-[1000] bg-white hover:bg-gray-100 p-3 rounded-full shadow-lg border border-gray-200 transition-all disabled:opacity-50"
                title="Get my location"
            >
                {loadingLocation ? (
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                ) : (
                    <Navigation className="w-6 h-6 text-blue-600" />
                )}
            </button>

            <MapContainer
                center={userLocation ? [userLocation.lat, userLocation.lng] : defaultCenter}
                zoom={13}
                scrollWheelZoom={true}
                className="h-full w-full"
                zoomControl={false}
                style={{ height: '100%', width: '100%' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <ZoomControl position="bottomright" />
                <MapController 
                    focusLocation={focusLocation} 
                    userLocation={userLocation}
                    locations={locations}
                />

                {/* User Location */}
                {userLocation && <UserLocation position={userLocation} />}

                {/* Location Markers */}
                {locations.map((loc, idx) => (
                    <Marker
                        key={idx}
                        position={[loc.lat, loc.lng]}
                        icon={getIconForCategory(loc.category || loc.type)}
                    >
                        <Popup className="custom-popup" maxWidth={300}>
                            <div className="p-2 min-w-[200px]">
                                {/* Header */}
                                <div className="border-b border-gray-100 pb-2 mb-2">
                                    <h3 className="font-bold text-gray-800 text-sm">{loc.name}</h3>
                                    <div className="flex items-center gap-1 mt-1">
                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                                            {loc.type || loc.category}
                                        </span>
                                        {loc.distance && (
                                            <span className="text-[10px] text-gray-500">
                                                • {loc.distance}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Details */}
                                <div className="space-y-1.5 mb-3">
                                    {loc.address && (
                                        <p className="text-[11px] text-gray-600 leading-relaxed flex items-start gap-1">
                                            <span className="text-gray-400 mt-0.5">📍</span>
                                            {loc.address}
                                        </p>
                                    )}
                                    {loc.phone && (
                                        <div className="flex items-center gap-1 text-[11px] text-gray-600">
                                            <Phone className="w-3 h-3 text-gray-400" />
                                            {String(loc.phone).replace('.0', '')}
                                        </div>
                                    )}
                                    {loc.hours && (
                                        <div className="flex items-center gap-1 text-[11px] text-gray-600">
                                            <Clock className="w-3 h-3 text-gray-400" />
                                            {loc.hours}
                                        </div>
                                    )}
                                    {loc.rating && (
                                        <div className="flex items-center gap-1 text-[11px] text-gray-600">
                                            <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                                            {loc.rating} / 5.0
                                        </div>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => getDirections(loc)}
                                        className="flex items-center justify-center gap-1 bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-semibold py-2 px-3 rounded-md transition-colors"
                                    >
                                        <Navigation className="w-3 h-3" />
                                        Directions
                                    </button>
                                    {loc.phone && (
                                        <a
                                            href={`tel:${String(loc.phone).replace(/[^0-9+]/g, '')}`}
                                            className="flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700 text-white text-[11px] font-semibold py-2 px-3 rounded-md transition-colors"
                                        >
                                            <Phone className="w-3 h-3" />
                                            Call
                                        </a>
                                    )}
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}

export default MapComponent;