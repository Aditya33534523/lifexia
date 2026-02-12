import React, { useState } from 'react';
import { Navigation, Phone, MapPin, Clock, Star, ExternalLink } from 'lucide-react';

function LocationList({ locations, onSelect, selectedId }) {
    const [sortBy, setSortBy] = useState('distance'); // distance, rating, name

    const getDirections = (e, loc) => {
        e.stopPropagation();
        const url = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}&destination_place_id=${encodeURIComponent(loc.name)}`;
        window.open(url, '_blank');
    };

    const callNumber = (e, phone) => {
        e.stopPropagation();
        window.location.href = `tel:${String(phone).replace(/[^0-9+]/g, '')}`;
    };

    // Sort locations
    const sortedLocations = [...locations].sort((a, b) => {
        if (sortBy === 'distance') {
            const distA = parseFloat(a.distance) || 999;
            const distB = parseFloat(b.distance) || 999;
            return distA - distB;
        } else if (sortBy === 'rating') {
            const ratingA = parseFloat(a.rating) || 0;
            const ratingB = parseFloat(b.rating) || 0;
            return ratingB - ratingA;
        } else {
            return (a.name || '').localeCompare(b.name || '');
        }
    });

    return (
        <div className="flex flex-col gap-3 p-4 h-full">
            {/* Header with Stats and Sort */}
            <div className="sticky top-0 bg-[#2d1b4e]/95 backdrop-blur-sm -mx-4 px-4 py-3 border-b border-white/10 z-10">
                <div className="flex items-center justify-between mb-2">
                    <div className="text-white/60 text-xs font-medium uppercase tracking-wider">
                        {locations.length} Location{locations.length !== 1 ? 's' : ''} Found
                    </div>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="text-[10px] bg-white/10 text-white border border-white/20 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-white/30"
                    >
                        <option value="distance" className="bg-[#2d1b4e] text-white">Distance</option>
                        <option value="rating" className="bg-[#2d1b4e] text-white">Rating</option>
                        <option value="name" className="bg-[#2d1b4e] text-white">Name</option>
                    </select>
                </div>
            </div>

            {/* Location Cards */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {sortedLocations.length === 0 ? (
                    <div className="text-white/40 text-center py-12 text-sm">
                        <MapPin className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>No locations match your filter.</p>
                        <p className="text-xs mt-2">Try adjusting your search criteria.</p>
                    </div>
                ) : (
                    sortedLocations.map((loc, idx) => (
                        <div
                            key={idx}
                            onClick={() => onSelect(loc)}
                            className={`glassmorphism rounded-2xl p-4 transition-all cursor-pointer group hover:bg-white/20 ${
                                selectedId === loc.name 
                                    ? 'ring-2 ring-blue-500/50 bg-white/15 shadow-lg shadow-blue-500/10' 
                                    : 'hover:shadow-xl'
                            }`}
                        >
                            {/* Header */}
                            <div className="flex justify-between items-start mb-2">
                                <div className="flex-1 pr-2">
                                    <h3 className="text-white font-semibold text-sm group-hover:text-blue-300 transition-colors line-clamp-2 leading-snug">
                                        {loc.name}
                                    </h3>
                                    <div className="flex items-center gap-2 mt-1">
                                        <p className="text-white/50 text-[10px] uppercase tracking-widest">
                                            {loc.type}
                                        </p>
                                        {loc.rating && (
                                            <div className="flex items-center gap-1">
                                                <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
                                                <span className="text-white/70 text-[10px] font-medium">
                                                    {loc.rating}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                {loc.distance && (
                                    <span className="text-white/80 text-[10px] font-medium bg-white/10 px-2.5 py-1 rounded-full border border-white/20 whitespace-nowrap">
                                        📍 {loc.distance}
                                    </span>
                                )}
                            </div>

                            {/* Details */}
                            <div className="space-y-1.5 mb-3">
                                {loc.address && (
                                    <div className="flex items-start text-white/50 text-[11px] leading-relaxed">
                                        <MapPin className="w-3 h-3 mr-2 mt-0.5 shrink-0 opacity-60" />
                                        <span className="line-clamp-2">{loc.address}</span>
                                    </div>
                                )}
                                {loc.phone && (
                                    <div className="flex items-center text-white/50 text-[11px]">
                                        <Phone className="w-3 h-3 mr-2 shrink-0 opacity-60" />
                                        <span>{String(loc.phone).replace('.0', '')}</span>
                                    </div>
                                )}
                                {loc.hours && (
                                    <div className="flex items-center text-white/50 text-[11px]">
                                        <Clock className="w-3 h-3 mr-2 shrink-0 opacity-60" />
                                        <span>{loc.hours}</span>
                                    </div>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={(e) => getDirections(e, loc)}
                                    className="flex items-center justify-center gap-1.5 py-2 px-3 bg-blue-600/30 hover:bg-blue-600/50 text-blue-200 text-[11px] font-medium rounded-xl border border-blue-500/30 transition-all group-hover:border-blue-400/40"
                                >
                                    <Navigation className="w-3 h-3" />
                                    <span>Directions</span>
                                </button>
                                
                                {loc.phone ? (
                                    <button
                                        onClick={(e) => callNumber(e, loc.phone)}
                                        className="flex items-center justify-center gap-1.5 py-2 px-3 bg-green-600/30 hover:bg-green-600/50 text-green-200 text-[11px] font-medium rounded-xl border border-green-500/30 transition-all group-hover:border-green-400/40"
                                    >
                                        <Phone className="w-3 h-3" />
                                        <span>Call</span>
                                    </button>
                                ) : (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onSelect(loc);
                                        }}
                                        className="flex items-center justify-center gap-1.5 py-2 px-3 bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 text-[11px] font-medium rounded-xl border border-purple-500/30 transition-all group-hover:border-purple-400/40"
                                    >
                                        <MapPin className="w-3 h-3" />
                                        <span>View Map</span>
                                    </button>
                                )}
                            </div>

                            {/* Tags/Categories if available */}
                            {loc.services && (
                                <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-white/10">
                                    {loc.services.slice(0, 3).map((service, i) => (
                                        <span key={i} className="text-[9px] px-2 py-0.5 rounded-full bg-white/5 text-white/60 border border-white/10">
                                            {service}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Footer Help Text */}
            {sortedLocations.length > 0 && (
                <div className="sticky bottom-0 bg-[#2d1b4e]/95 backdrop-blur-sm -mx-4 px-4 py-2 border-t border-white/10">
                    <p className="text-white/40 text-[10px] text-center">
                        💡 Click on a location to view it on the map
                    </p>
                </div>
            )}
        </div>
    );
}

export default LocationList;