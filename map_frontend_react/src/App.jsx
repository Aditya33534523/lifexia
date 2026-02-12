import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import LocationList from './components/LocationList';
import { Filter, MapPin, Loader } from 'lucide-react';

const API_BASE = '/api/map';

function App() {
    const [locations, setLocations] = useState([]);
    const [filteredLocations, setFilteredLocations] = useState([]);
    const [currentCategory, setCurrentCategory] = useState('All');
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [userLocation, setUserLocation] = useState(null);
    const [loadingNearby, setLoadingNearby] = useState(false);

    const categories = ['All', 'Hospital', 'Pharmacy', 'Gynecologist', 'Orthopedic', 'Pediatrician', 'General Physician'];

    useEffect(() => {
        loadLocations();
    }, []);

    const loadLocations = async (enrich = false) => {
        try {
            const res = await fetch(`${API_BASE}/locations?enrich=${enrich}`);
            const data = await res.json();
            setLocations(data);
            setFilteredLocations(data);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching locations:", err);
            setLoading(false);
        }
    };

    const loadNearbyPlaces = async (lat, lng, type = 'pharmacy') => {
        setLoadingNearby(true);
        try {
            const res = await fetch(`${API_BASE}/search-nearby?lat=${lat}&lng=${lng}&type=${type}&radius=5000`);
            const data = await res.json();
            
            // Merge with existing locations
            const merged = [...locations, ...data];
            setLocations(merged);
            setFilteredLocations(merged);
        } catch (err) {
            console.error("Error loading nearby places:", err);
        }
        setLoadingNearby(false);
    };

    const handleFilterChange = (category) => {
        setCurrentCategory(category);
        if (category === 'All') {
            setFilteredLocations(locations);
        } else {
            setFilteredLocations(locations.filter(loc =>
                loc.category === category || (loc.type && loc.type.includes(category))
            ));
        }
        setSelectedLocation(null);
    };

    const handleLocationSelect = (loc) => {
        setSelectedLocation(loc);
    };

    if (loading) {
        return (
            <div className="h-screen w-full flex items-center justify-center bg-[#2d1b4e]">
                <div className="text-center">
                    <Loader className="w-12 h-12 text-white animate-spin mx-auto mb-4" />
                    <p className="text-white">Loading medical facilities...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full flex bg-[#2d1b4e] overflow-hidden">
            {/* Sidebar */}
            <div className="w-80 h-full flex flex-col border-r border-white/10 z-20 glassmorphism relative shrink-0">
                {/* Header */}
                <div className="p-4 border-b border-white/10 shrink-0">
                    <div className="flex items-center gap-2 mb-3">
                        <MapPin className="w-5 h-5 text-white" />
                        <h2 className="text-white font-semibold text-lg">Medical Facilities</h2>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-white/70" />
                        <select
                            value={currentCategory}
                            onChange={(e) => handleFilterChange(e.target.value)}
                            className="flex-1 bg-white/10 text-white text-xs border border-white/20 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-white/30"
                        >
                            {categories.map(cat => 
                                <option key={cat} value={cat} className="bg-[#2d1b4e] text-white">
                                    {cat}
                                </option>
                            )}
                        </select>
                    </div>
                    
                    {loadingNearby && (
                        <div className="mt-2 text-xs text-white/70 flex items-center gap-2">
                            <Loader className="w-3 h-3 animate-spin" />
                            Loading nearby places...
                        </div>
                    )}
                </div>

                {/* List */}
                <div className="flex-1 overflow-hidden">
                    <LocationList
                        locations={filteredLocations}
                        onSelect={handleLocationSelect}
                        selectedId={selectedLocation?.name}
                    />
                </div>
            </div>

            {/* Map */}
            <div className="flex-1 relative z-10">
                <MapComponent
                    locations={filteredLocations}
                    focusLocation={selectedLocation}
                    onLocationDetected={setUserLocation}
                    onNearbySearch={loadNearbyPlaces}
                />
            </div>
        </div>
    );
}

export default App;