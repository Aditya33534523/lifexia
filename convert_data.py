
import pandas as pd
import json
import os
import random

def convert_excel_to_json():
    # File path
    excel_path = "Hospital data (1).xlsx"
    output_path = "frontend/static/js/locations.json"

    if not os.path.exists(excel_path):
        print(f"Error: {excel_path} not found.")
        return

    try:
        # read excel
        df = pd.read_excel(excel_path)
        
        # inspected columns: ['Area', 'Hospital', 'Speciality', 'contact number', 'gov. certifications', 'Mediclaims', 'Cashless', 'AYUSHMAN CARD ']
        
        locations = []
        # Base coordinates for Ahmedabad (approx center) to generate random offsets if missing
        base_lat = 23.0225
        base_lng = 72.5714
        
        for index, row in df.iterrows():
            name = row.get('Hospital')
            if pd.isna(name):
                continue
                
            # Category mapping
            # 'Speciality' column likely contains things like 'Ortho', 'Gynec', etc.
            speciality = str(row.get('Speciality', '')).lower()
            category = 'Hospital' # Default
            
            if 'gynec' in speciality or 'maternity' in speciality:
                category = 'Gynecologist'
            elif 'ortho' in speciality or 'bone' in speciality:
                category = 'Orthopedic'
            elif 'pedia' in speciality or 'child' in speciality:
                category = 'Pediatrician'
            elif 'pharmacy' in speciality or 'medical' in speciality:
                category = 'Pharmacy'
            elif 'physician' in speciality or 'general' in speciality:
                category = 'General Physician'
            
            # Contact
            phone = str(row.get('contact number', '')).replace('nan', '').strip()
            
            # Address/Area
            area = str(row.get('Area', '')).replace('nan', '').strip()
            
            # Coordinates - Missing in file, so generating dummy near Ahmedabad for demo
            # In production, would use Geocoding API
            lat = base_lat + (random.random() - 0.5) * 0.1
            lng = base_lng + (random.random() - 0.5) * 0.1
            
            locations.append({
                "name": name,
                "type": str(row.get('Speciality', 'Hospital')).replace('nan', 'Hospital'),
                "category": category,
                "lat": lat,
                "lng": lng,
                "phone": phone,
                "address": area,
                "distance": f"{round(random.uniform(0.5, 5.0), 1)} km" # Dummy distance
            })
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(locations, f, indent=4)
            
        print(f"Successfully converted {len(locations)} locations to {output_path}")

    except Exception as e:
        print(f"Error converting: {e}")

if __name__ == "__main__":
    convert_excel_to_json()
