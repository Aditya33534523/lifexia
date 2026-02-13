from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

map_bp = Blueprint('map', __name__)

@map_bp.route('/nearby-hospitals', methods=['GET'])
def get_nearby_hospitals():
    """Get nearby hospitals based on user location"""
    try:
        # Get parameters
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=20, type=float)
        speciality = request.args.get('speciality')
        ayushman = request.args.get('ayushman', default=False, type=lambda v: v.lower() == 'true')
        maa = request.args.get('maa', default=False, type=lambda v: v.lower() == 'true')
        emergency = request.args.get('emergency', default=False, type=lambda v: v.lower() == 'true')
        
        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude are required'
            }), 400
        
        map_service = current_app.config.get('MAP_SERVICE')
        
        if not map_service:
            return jsonify({
                'success': False,
                'error': 'Map service unavailable'
            }), 503
        
        hospitals = map_service.get_nearby_hospitals(
            user_lat=lat,
            user_lon=lon,
            radius_km=radius,
            speciality=speciality,
            ayushman_only=ayushman,
            maa_only=maa,
            emergency_only=emergency
        )
        
        return jsonify({
            'success': True,
            'count': len(hospitals),
            'hospitals': hospitals
        })
        
    except Exception as e:
        logger.error(f"Nearby hospitals error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve hospitals'
        }), 500

@map_bp.route('/nearby-pharmacies', methods=['GET'])
def get_nearby_pharmacies():
    """Get nearby pharmacies"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=10, type=float)
        open_now = request.args.get('open_now', default=False, type=lambda v: v.lower() == 'true')
        
        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': 'Location required'
            }), 400
        
        map_service = current_app.config.get('MAP_SERVICE')
        
        pharmacies = map_service.get_nearby_pharmacies(
            user_lat=lat,
            user_lon=lon,
            radius_km=radius,
            open_now=open_now
        )
        
        return jsonify({
            'success': True,
            'count': len(pharmacies),
            'pharmacies': pharmacies
        })
        
    except Exception as e:
        logger.error(f"Nearby pharmacies error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve pharmacies'
        }), 500

@map_bp.route('/hospital/<hospital_id>', methods=['GET'])
def get_hospital_details(hospital_id):
    """Get detailed hospital information"""
    try:
        map_service = current_app.config.get('MAP_SERVICE')
        hospital = map_service.get_hospital_by_id(hospital_id)
        
        if hospital:
            # Add user location if provided for distance calculation
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)
            
            if lat and lon:
                distance = map_service.calculate_distance(lat, lon, hospital['latitude'], hospital['longitude'])
                hospital['distance_km'] = distance
                hospital['estimated_time_min'] = round((distance / 40) * 60)
                hospital['google_maps_link'] = map_service.get_google_maps_link(
                    hospital['latitude'],
                    hospital['longitude'],
                    hospital['name']
                )
            
            return jsonify({
                'success': True,
                'hospital': hospital
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Hospital not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Hospital details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve hospital details'
        }), 500

@map_bp.route('/directions', methods=['POST'])
def get_directions():
    """Generate Google Maps directions link"""
    try:
        data = request.json
        dest_lat = data.get('latitude')
        dest_lon = data.get('longitude')
        place_name = data.get('name', '')
        
        if not dest_lat or not dest_lon:
            return jsonify({
                'success': False,
                'error': 'Destination coordinates required'
            }), 400
        
        map_service = current_app.config.get('MAP_SERVICE')
        maps_link = map_service.get_google_maps_link(dest_lat, dest_lon, place_name)
        
        return jsonify({
            'success': True,
            'google_maps_link': maps_link
        })
        
    except Exception as e:
        logger.error(f"Directions error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate directions'
        }), 500

@map_bp.route('/search', methods=['GET'])
def search_facilities():
    """Search for hospitals/pharmacies by name or speciality"""
    try:
        query = request.args.get('q', '').strip()
        facility_type = request.args.get('type')  # HOSPITAL or PHARMACY
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400
        
        map_service = current_app.config.get('MAP_SERVICE')
        results = map_service.search_facilities(query, facility_type)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500

@map_bp.route('/emergency', methods=['GET'])
def get_emergency_hospitals():
    """Get all emergency hospitals, sorted by distance if location provided"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        map_service = current_app.config.get('MAP_SERVICE')
        emergency_hospitals = map_service.get_emergency_hospitals(lat, lon)
        
        return jsonify({
            'success': True,
            'count': len(emergency_hospitals),
            'hospitals': emergency_hospitals,
            'emergency_number': '108'  # India emergency number
        })
        
    except Exception as e:
        logger.error(f"Emergency hospitals error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve emergency hospitals'
        }), 500

@map_bp.route('/card-facilities', methods=['GET'])
def get_card_facilities():
    """Get facilities accepting Ayushman/MAA cards"""
    try:
        ayushman = request.args.get('ayushman', default=False, type=lambda v: v.lower() == 'true')
        maa = request.args.get('maa', default=False, type=lambda v: v.lower() == 'true')
        
        map_service = current_app.config.get('MAP_SERVICE')
        facilities = map_service.get_facilities_with_cards(ayushman, maa)
        
        return jsonify({
            'success': True,
            'count': len(facilities),
            'facilities': facilities
        })
        
    except Exception as e:
        logger.error(f"Card facilities error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve facilities'
        }), 500