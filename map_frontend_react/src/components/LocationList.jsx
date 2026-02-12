import React from 'react';
import { Navigation, Phone, MapPin } from 'lucide-react';

function LocationList({ locations, onSelect, selectedId }) {
    const getDirections = (e, loc) => {
        e.stopPropagation();
        const url = `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}&destination_place_id=${encodeURIComponent(loc.name)}`;
        window.open(url, '_blank');
    };

    return (
        <div className="flex flex-col gap-3 p-4">
            <div className="text-white/60 text-xs font-medium uppercase tracking-wider mb-2">
                {locations.length} Locations Found
            </div>

            {locations.length === 0 ? (
                <div className="text-white/40 text-center py-8 text-sm">No locations match your filter.</div>
            ) : (
                locations.map((loc, idx) => (
                    <div
                        key={idx}
                        onClick={() => onSelect(loc)}
                        className={`glassmorphism rounded-2xl p-4 transition-all cursor-pointer group hover:bg-white/20 ${selectedId === loc.name ? 'ring-2 ring-blue-500/50 bg-white/10' : ''
                            }`}
                    >
                        <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                                <h3 className="text-white font-semibold text-sm group-hover:text-blue-300 transition-colors line-clamp-1">
                                    {loc.name}
                                </h3>
                                <p className="text-white/50 text-[10px] uppercase tracking-widest mt-0.5">
                                    {loc.type}
                                </p>
                            </div>
                            {loc.distance && (
                                <span className="text-white/80 text-[10px] bg-white/5 px-2 py-0.5 rounded-full border border-white/10">
                                    {loc.distance}
                                </span>
                            )}
                        </div>

                        <div className="space-y-1.5 mb-3">
                            {loc.address && (
                                <div className="flex items-start text-white/50 text-[11px]">
                                    <MapPin className="w-3 h-3 mr-2 mt-0.5 shrink-0" />
                                    <span className="line-clamp-2 leading-relaxed">{loc.address}</span>
                                </div>
                            )}
                            {loc.phone && (
                                <div className="flex items-center text-white/50 text-[11px]">
                                    <Phone className="w-3 h-3 mr-2 shrink-0" />
                                    {String(loc.phone).replace('.0', '')}
                                </div>
                            )}
                        </div>

                        <button
                            onClick={(e) => getDirections(e, loc)}
                            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 text-xs font-medium rounded-xl border border-blue-500/30 transition-all"
                        >
                            <Navigation className="w-3 h-3" />
                            Get Directions
                        </button>
                    </div>
                ))
            )}
        </div>
    );
}

export default LocationList;
