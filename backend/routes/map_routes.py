from flask import Blueprint, jsonify, current_app
from backend.services.google_places_service import GooglePlacesService
import json
import os

map_bp = Blueprint('map', __name__, url_prefix='/api/map')

@map_bp.route('/locations')
def get_locations():
    try:
        locations_path = os.path.join(current_app.root_path, '..', 'frontend', 'static', 'js', 'locations.json')
        
        if not os.path.exists(locations_path):
            return jsonify({"error": "Locations data not found"}), 404
            
        with open(locations_path, 'r') as f:
            data = json.load(f)
        
        # Optional: Enrich with Google Places data
        enrich = request.args.get('enrich', 'false').lower() == 'true'
        if enrich and os.getenv('GOOGLE_PLACES_API_KEY'):
            places_service = GooglePlacesService()
            data = places_service.enrich_location_data(data)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@map_bp.route('/search-nearby')
def search_nearby():
    """Search for nearby medical facilities using Google Places"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 5000, type=int)
    place_type = request.args.get('type', 'pharmacy')
    
    if not lat or not lng:
        return jsonify({"error": "lat and lng parameters required"}), 400
    
    if not os.getenv('GOOGLE_PLACES_API_KEY'):
        return jsonify({"error": "Google Places API not configured"}), 500
    
    places_service = GooglePlacesService()
    results = places_service.search_nearby(lat, lng, radius, place_type)
    
    # Convert to our format
    locations = []
    for place in results:
        geometry = place.get('geometry', {}).get('location', {})
        locations.append({
            'name': place.get('name'),
            'type': place_type.title(),
            'category': place_type.title(),
            'lat': geometry.get('lat'),
            'lng': geometry.get('lng'),
            'rating': place.get('rating'),
            'address': place.get('vicinity'),
            'place_id': place.get('place_id'),
            'is_open': place.get('opening_hours', {}).get('open_now')
        })
    
    return jsonify(locations)