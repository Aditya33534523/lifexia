from flask import Blueprint, jsonify, current_app
import json
import os

map_bp = Blueprint('map', __name__, url_prefix='/api/map')

@map_bp.route('/locations')
def get_locations():
    try:
        # Path to locations.json in the static folder
        locations_path = os.path.join(current_app.root_path, '..', 'frontend', 'static', 'js', 'locations.json')
        
        if not os.path.exists(locations_path):
            return jsonify({"error": "Locations data not found"}), 404
            
        with open(locations_path, 'r') as f:
            data = json.load(f)
            
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
