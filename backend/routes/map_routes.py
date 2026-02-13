from flask import Blueprint, request, jsonify
import logging
import math

logger = logging.getLogger(__name__)

map_bp = Blueprint('map', __name__, url_prefix='/api/map')

# Featured hospitals data (can be moved to database later)
FEATURED_HOSPITALS = [
    {
        "id": "elite",
        "name": "Elite Orthopaedic & Womens Hospital",
        "lat": 23.0175,
        "lng": 72.4822,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "Orthopaedic & Womens",
        "certs": "NABH Certified",
        "contact": "9824623823",
        "cashless": "No",
        "benefit": "Advanced Orthopaedic & Gynaecology Care",
        "ayushmanCard": True,
        "maaCard": True,
        "address": "Ahmedabad, Gujarat",
        "services": ["Emergency", "ICU", "Surgery", "Diagnostics"]
    },
    {
        "id": "sannidhya",
        "name": "Sannidhya Gynaec Hospital",
        "lat": 22.9962,
        "lng": 72.5996,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "Gynaecology",
        "certs": "Multispeciality",
        "contact": "7575890555",
        "cashless": "Yes",
        "benefit": "Comprehensive Women's Healthcare",
        "ayushmanCard": True,
        "maaCard": True,
        "address": "Ahmedabad, Gujarat",
        "services": ["Maternity", "Gynaecology", "Pediatrics"]
    },
    {
        "id": "khusboo",
        "name": "Khusboo Orthopaedic Hospital",
        "lat": 23.0200,
        "lng": 72.5081,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "Orthopaedic",
        "certs": "Specialist Care",
        "contact": "7575890555",
        "cashless": "Yes",
        "benefit": "Expert Orthopaedic Surgery",
        "ayushmanCard": True,
        "maaCard": False,
        "address": "Ahmedabad, Gujarat",
        "services": ["Orthopaedic Surgery", "Physiotherapy", "Sports Medicine"]
    },
    {
        "id": "star",
        "name": "Star Hospital",
        "lat": 23.0374,
        "lng": 72.6300,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "Multispeciality",
        "certs": "Government Approved",
        "contact": "9898394943",
        "cashless": "Yes (12 companies)",
        "benefit": "24/7 Emergency & Critical Care",
        "ayushmanCard": True,
        "maaCard": True,
        "address": "Ahmedabad, Gujarat",
        "services": ["Emergency", "ICU", "Surgery", "Cardiology", "Neurology"]
    },
    {
        "id": "vanza",
        "name": "Vanza Hospital",
        "lat": 23.0450,
        "lng": 72.5150,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "General",
        "certs": "Multi-specialty",
        "contact": "9898123456",
        "cashless": "Yes",
        "benefit": "General Healthcare Services",
        "ayushmanCard": True,
        "maaCard": False,
        "address": "Ahmedabad, Gujarat",
        "services": ["General Medicine", "Surgery", "Diagnostics"]
    },
    {
        "id": "shreeji",
        "name": "Shreeji Children Hospital",
        "lat": 23.0100,
        "lng": 72.5500,
        "type": "HOSPITAL",
        "category": "Hospital",
        "speciality": "Pediatrics",
        "certs": "Pediatric Specialist",
        "contact": "9898234567",
        "cashless": "Yes",
        "benefit": "Specialized Pediatric Care",
        "ayushmanCard": True,
        "maaCard": True,
        "address": "Ahmedabad, Gujarat",
        "services": ["Pediatrics", "Neonatal Care", "Vaccination"]
    }
]


def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)


@map_bp.route('/locations', methods=['GET'])
def get_locations():
    """
    Get all healthcare locations with optional filtering and distance calculation.
    """
    try:
        # Get query parameters
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        category_filter = request.args.get('category')
        speciality_filter = request.args.get('speciality')
        radius_filter = request.args.get('radius', type=float)
        ayushman_filter = request.args.get('ayushman', '').lower() == 'true'
        maa_filter = request.args.get('maa', '').lower() == 'true'
        
        locations = FEATURED_HOSPITALS.copy()
        
        # Calculate distances if user location provided
        if user_lat is not None and user_lng is not None:
            for location in locations:
                distance = calculate_distance(user_lat, user_lng, location['lat'], location['lng'])
                location['distance'] = distance
                # Estimate travel time (assuming 40 km/h average speed)
                location['estimatedTime'] = round((distance / 40) * 60)  # in minutes
            
            # Sort by distance
            locations.sort(key=lambda x: x.get('distance', float('inf')))
        
        # Apply filters
        filtered_locations = locations
        
        if category_filter and category_filter.upper() != 'ALL RESOURCES':
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('category', '').lower() == category_filter.lower() or 
                   loc.get('type', '').lower() == category_filter.lower()
            ]
        
        if speciality_filter:
            filtered_locations = [
                loc for loc in filtered_locations 
                if speciality_filter.lower() in loc.get('speciality', '').lower()
            ]
        
        if radius_filter and user_lat is not None:
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('distance', float('inf')) <= radius_filter
            ]
        
        if ayushman_filter:
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('ayushmanCard', False)
            ]
        
        if maa_filter:
            filtered_locations = [
                loc for loc in filtered_locations 
                if loc.get('maaCard', False)
            ]
        
        return jsonify({
            'success': True,
            'count': len(filtered_locations),
            'locations': filtered_locations,
            'filters_applied': {
                'category': category_filter,
                'speciality': speciality_filter,
                'radius': radius_filter,
                'ayushman': ayushman_filter,
                'maa': maa_filter
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to fetch locations',
            'message': str(e)
        }), 500


@map_bp.route('/locations/<location_id>', methods=['GET'])
def get_location_details(location_id):
    """Get detailed information about a specific location"""
    try:
        location = next((loc for loc in FEATURED_HOSPITALS if loc['id'] == location_id), None)
        
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location not found'
            }), 404
        
        # Calculate distance if user location provided
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        
        location_data = location.copy()
        
        if user_lat is not None and user_lng is not None:
            distance = calculate_distance(user_lat, user_lng, location['lat'], location['lng'])
            location_data['distance'] = distance
            location_data['estimatedTime'] = round((distance / 40) * 60)
        
        return jsonify({
            'success': True,
            'location': location_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching location details: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to fetch location details',
            'message': str(e)
        }), 500


@map_bp.route('/search', methods=['GET'])
def search_locations():
    """Search locations by name or specialty"""
    try:
        query = request.args.get('q', '').lower()
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400
        
        # Search in name, speciality, and services
        results = []
        for location in FEATURED_HOSPITALS:
            if (query in location['name'].lower() or 
                query in location.get('speciality', '').lower() or
                any(query in service.lower() for service in location.get('services', []))):
                
                loc_data = location.copy()
                
                # Calculate distance if user location provided
                if user_lat is not None and user_lng is not None:
                    distance = calculate_distance(user_lat, user_lng, location['lat'], location['lng'])
                    loc_data['distance'] = distance
                    loc_data['estimatedTime'] = round((distance / 40) * 60)
                
                results.append(loc_data)
        
        # Sort by distance if available
        if user_lat is not None:
            results.sort(key=lambda x: x.get('distance', float('inf')))
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching locations: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500