import React, { useState, useEffect } from 'react';
import MapComponent from './components/MapComponent';
import LocationList from './components/LocationList';
import { Filter } from 'lucide-react';

const API_BASE = '/api/map';

function App() {
    const [locations, setLocations] = useState([]);
    const [filteredLocations, setFilteredLocations] = useState([]);
    const [currentCategory, setCurrentCategory] = useState('All');
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [loading, setLoading] = useState(true);

    const categories = ['All', 'Hospital', 'Pharmacy', 'Gynecologist', 'Orthopedic', 'Pediatrician', 'General Physician'];

    useEffect(() => {
        fetch(`${API_BASE}/locations`)
            .then(res => res.json())
            .then(data => {
                setLocations(data);
                setFilteredLocations(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching locations:", err);
                setLoading(false);
            });
    }, []);

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
            <div className="h-screen w-full flex items-center justify-center bg-[#2d1b4e] text-white">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white"></div>
            </div>
        );
    }

    return (
        <div className="h-screen w-full flex bg-[#2d1b4e] overflow-hidden">
            {/* Sidebar - Location List */}
            <div className="w-80 h-full flex flex-col border-r border-white/10 z-20 glassmorphism relative shrink-0">
                <div className="p-4 border-b border-white/10 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-white/70" />
                        <select
                            value={currentCategory}
                            onChange={(e) => handleFilterChange(e.target.value)}
                            className="bg-white/10 text-white text-xs border border-white/20 rounded-lg px-2 py-1 focus:outline-none"
                        >
                            {categories.map(cat => <option key={cat} value={cat} className="bg-[#2d1b4e] text-white">{cat}</option>)}
                        </select>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    <LocationList
                        locations={filteredLocations}
                        onSelect={handleLocationSelect}
                        selectedId={selectedLocation?.name}
                    />
                </div>
            </div>

            {/* Map Container - Full Right Side */}
            <div className="flex-1 relative z-10">
                <MapComponent
                    locations={filteredLocations}
                    focusLocation={selectedLocation}
                />
            </div>
        </div>
    );
}

export default App;
