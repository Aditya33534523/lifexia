import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, ZoomControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet icon paths in React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Custom Hospital Icon
const hospitalIcon = L.icon({
    iconUrl: '/hospital-pin.png', // Assuming it's in public folder
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
});

// Helper component to handle focusing/centering
function MapResizer({ focusLocation }) {
    const map = useMap();

    useEffect(() => {
        // Force invalidationsize when component mounts
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
        }
    }, [focusLocation, map]);

    return null;
}

function MapComponent({ locations, focusLocation }) {
    const defaultCenter = [23.0225, 72.5714]; // Ahmedabad

    return (
        <div className="h-full w-full" style={{ height: '100vh', width: '100%' }}>
            <MapContainer
                center={defaultCenter}
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
                <MapResizer focusLocation={focusLocation} />

                {locations.map((loc, idx) => (
                    <Marker
                        key={idx}
                        position={[loc.lat, loc.lng]}
                        icon={(loc.category === 'Hospital' || loc.type === 'Hospital') ? hospitalIcon : DefaultIcon}
                    >
                        <Popup className="custom-popup">
                            <div className="p-1 min-w-[150px]">
                                <h3 className="font-bold text-gray-800 border-b border-gray-100 pb-2 mb-2">{loc.name}</h3>
                                <p className="text-xs text-gray-500 mb-1 leading-relaxed">{loc.type}</p>
                                {loc.address && <p className="text-[10px] text-gray-400 mb-2 leading-relaxed italic">{loc.address}</p>}
                                <button
                                    onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`, '_blank')}
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-semibold py-1.5 rounded-md transition-colors"
                                >
                                    Directions
                                </button>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}

export default MapComponent;
