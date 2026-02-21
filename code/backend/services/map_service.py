"""
LIFEXIA Map Service - Hospital & Pharmacy Location System
Provides nearby facility search, distance calculation, filtering by cards, specialties, etc.
"""

import math
import json
import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MapService:
    """Service for managing hospital/pharmacy locations and proximity search"""

    def __init__(self, data_file: Optional[str] = None):
        self.facilities = []
        self._load_data(data_file)
        logger.info(f"MapService initialized with {len(self.facilities)} facilities")

    def _load_data(self, data_file: Optional[str] = None):
        """Load facility data from JSON or use built-in dataset"""
        if data_file and os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    self.facilities = json.load(f)
                return
            except Exception as e:
                logger.error(f"Failed to load data file: {e}")

        # Check static location.json
        static_json = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'static', 'js', 'location.json'
        )
        if os.path.exists(static_json):
            try:
                with open(static_json, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.facilities = json.load(open(static_json, 'r'))
                        if self.facilities:
                            return
            except Exception:
                pass

        # Built-in comprehensive hospital/pharmacy dataset (Ahmedabad region)
        self.facilities = [
            {
                "id": "h001",
                "name": "Elite Orthopaedic & Womens Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Orthopaedic",
                "lat": 23.0258,
                "lng": 72.5873,
                "address": "Navrangpura, Ahmedabad, Gujarat 380009",
                "contact": "+91-79-26560123",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["ICICI Lombard", "Star Health", "HDFC Ergo"],
                "services": ["Orthopaedic Surgery", "Joint Replacement", "Gynaecology", "Maternity", "Emergency"],
                "certifications": ["NABH"],
                "ratings": 4.5,
                "benefit": "Advanced joint replacement center with robotic-assisted surgery. Cashless treatment with major insurance providers.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h002",
                "name": "Sannidhya Gynaec Hospital",
                "type": "HOSPITAL",
                "category": "Specialty",
                "speciality": "Gynaecology",
                "lat": 23.0150,
                "lng": 72.5560,
                "address": "Chekla Goplnagar, Ahmedabad, Gujarat 380015",
                "contact": "+91-79-26340567",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": True,
                "cashlessCompanies": ["Star Health", "New India Assurance"],
                "services": ["Gynaecology", "Obstetrics", "Maternity", "IVF", "Laparoscopy"],
                "certifications": [],
                "ratings": 4.3,
                "benefit": "Specialized women's healthcare. Accepts Ayushman Bharat & MAA Vatsalya cards for cashless maternity care.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h003",
                "name": "Khusboo Orthopaedic Hospital",
                "type": "HOSPITAL",
                "category": "Specialty",
                "speciality": "Orthopaedic",
                "lat": 23.0320,
                "lng": 72.5650,
                "address": "Ghatlodia, Ahmedabad, Gujarat 380061",
                "contact": "+91-79-27430890",
                "emergency": True,
                "open24x7": False,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["ICICI Lombard", "Bajaj Allianz"],
                "services": ["Orthopaedic Surgery", "Fracture Treatment", "Physiotherapy", "Spine Surgery"],
                "certifications": [],
                "ratings": 4.2,
                "benefit": "Expert fracture & spine care. Cashless with Ayushman Bharat card.",
                "openingHours": {"weekday": "8:00-20:00", "weekend": "9:00-14:00"}
            },
            {
                "id": "h004",
                "name": "Star Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0180,
                "lng": 72.5700,
                "address": "Naranpura, Ahmedabad, Gujarat 380013",
                "contact": "+91-79-27560456",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": True,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Max Bupa"],
                "services": ["Cardiology", "Neurology", "Orthopaedics", "Emergency", "ICU", "Paediatrics"],
                "certifications": ["NABH", "NABL"],
                "ratings": 4.6,
                "benefit": "Full-service multi-specialty hospital. NABH accredited with 24/7 emergency and ICU facilities.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h005",
                "name": "Vanza Hospital",
                "type": "HOSPITAL",
                "category": "General",
                "speciality": "Multispeciality",
                "lat": 23.0095,
                "lng": 72.5520,
                "address": "Nava Vadaj, Ahmedabad, Gujarat 380013",
                "contact": "+91-79-29290345",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": False,
                "maaCard": True,
                "cashlessCompanies": ["New India Assurance"],
                "services": ["General Medicine", "Surgery", "Maternity", "Paediatrics", "Emergency"],
                "certifications": [],
                "ratings": 4.0,
                "benefit": "Affordable multi-specialty care. MAA Vatsalya card accepted for maternity services.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h006",
                "name": "Shreeji Children Hospital",
                "type": "HOSPITAL",
                "category": "Specialty",
                "speciality": "Pediatrics",
                "lat": 23.0050,
                "lng": 72.5480,
                "address": "Ranip, Ahmedabad, Gujarat 382480",
                "contact": "+91-79-27550198",
                "emergency": True,
                "open24x7": False,
                "ayushmanCard": True,
                "maaCard": True,
                "cashlessCompanies": ["Star Health", "ICICI Lombard"],
                "services": ["Paediatrics", "Neonatology", "Child Surgery", "Vaccination"],
                "certifications": [],
                "ratings": 4.4,
                "benefit": "Dedicated children's hospital with NICU facility. Ayushman & MAA cards accepted.",
                "openingHours": {"weekday": "8:00-21:00", "weekend": "9:00-18:00"}
            },
            {
                "id": "h007",
                "name": "Civil Hospital Ahmedabad",
                "type": "HOSPITAL",
                "category": "Government",
                "speciality": "Multispeciality",
                "lat": 23.0450,
                "lng": 72.5980,
                "address": "Asarwa, Ahmedabad, Gujarat 380016",
                "contact": "+91-79-22683721",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": True,
                "cashlessCompanies": [],
                "services": ["All Specialties", "Trauma Center", "Emergency", "ICU", "Blood Bank", "Radiology"],
                "certifications": ["NABH"],
                "ratings": 3.8,
                "benefit": "Largest government hospital in Gujarat. Free treatment under Ayushman Bharat. All specialties available.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h008",
                "name": "SAL Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0520,
                "lng": 72.5350,
                "address": "Drive-In Road, Ahmedabad, Gujarat 380054",
                "contact": "+91-79-40200200",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Bajaj Allianz", "Max Bupa"],
                "services": ["Cardiac Surgery", "Neurosurgery", "Orthopaedics", "Oncology", "Gastroenterology"],
                "certifications": ["NABH", "NABL"],
                "ratings": 4.7,
                "benefit": "Premier multi-specialty hospital. Advanced cardiac care center with robotic surgery capabilities.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h009",
                "name": "Zydus Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0700,
                "lng": 72.5170,
                "address": "SG Highway, Ahmedabad, Gujarat 380054",
                "contact": "+91-79-66190000",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Bajaj Allianz", "Tata AIG"],
                "services": ["Cardiology", "Transplant", "Oncology", "Neurosurgery", "Emergency", "Robotics"],
                "certifications": ["NABH", "JCI"],
                "ratings": 4.8,
                "benefit": "JCI accredited international-standard hospital. Organ transplant center. Proton therapy for cancer.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h010",
                "name": "Apollo Hospital Ahmedabad",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0380,
                "lng": 72.5090,
                "address": "Bhat, GIFT City Road, Ahmedabad, Gujarat",
                "contact": "+91-79-66701800",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Bajaj Allianz", "Max Bupa", "Tata AIG"],
                "services": ["All Specialties", "Robotic Surgery", "Transplant", "Emergency", "Heart Center"],
                "certifications": ["NABH", "JCI"],
                "ratings": 4.7,
                "benefit": "Part of Apollo Hospitals chain. International quality healthcare with 24/7 emergency services.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h011",
                "name": "Shalby Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Orthopaedic",
                "lat": 23.0130,
                "lng": 72.5310,
                "address": "S.G. Highway, Ahmedabad, Gujarat 380015",
                "contact": "+91-79-40500500",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo"],
                "services": ["Joint Replacement", "Spine Surgery", "Orthopaedics", "Physiotherapy", "Sports Medicine"],
                "certifications": ["NABH"],
                "ratings": 4.5,
                "benefit": "India's leading joint replacement hospital. Over 1 lakh successful surgeries performed.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "p001",
                "name": "MedPlus Pharmacy - Navrangpura",
                "type": "PHARMACY",
                "category": "Retail Pharmacy",
                "speciality": "Pharmacy",
                "lat": 23.0280,
                "lng": 72.5850,
                "address": "Navrangpura, Ahmedabad, Gujarat 380009",
                "contact": "+91-79-26560999",
                "emergency": False,
                "open24x7": False,
                "ayushmanCard": False,
                "maaCard": False,
                "cashlessCompanies": [],
                "services": ["Prescription Medicines", "OTC Medicines", "Health Products", "Home Delivery"],
                "certifications": [],
                "ratings": 4.1,
                "benefit": "Trusted pharmacy chain. Home delivery available. Genuine medicines guaranteed.",
                "openingHours": {"weekday": "8:00-22:00", "weekend": "9:00-21:00"}
            },
            {
                "id": "p002",
                "name": "Apollo Pharmacy - CG Road",
                "type": "PHARMACY",
                "category": "Retail Pharmacy",
                "speciality": "Pharmacy",
                "lat": 23.0300,
                "lng": 72.5620,
                "address": "CG Road, Ahmedabad, Gujarat 380006",
                "contact": "+91-79-26460333",
                "emergency": False,
                "open24x7": True,
                "ayushmanCard": False,
                "maaCard": False,
                "cashlessCompanies": [],
                "services": ["Prescription Medicines", "OTC Medicines", "Diagnostics", "Home Delivery"],
                "certifications": [],
                "ratings": 4.3,
                "benefit": "24/7 pharmacy service. Part of Apollo chain. Diagnostic services available.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "p003",
                "name": "Netmeds Pharmacy - Ghatlodia",
                "type": "PHARMACY",
                "category": "Retail Pharmacy",
                "speciality": "Pharmacy",
                "lat": 23.0340,
                "lng": 72.5430,
                "address": "Ghatlodia, Ahmedabad, Gujarat 380061",
                "contact": "+91-79-27430555",
                "emergency": False,
                "open24x7": False,
                "ayushmanCard": False,
                "maaCard": False,
                "cashlessCompanies": [],
                "services": ["Prescription Medicines", "OTC Medicines", "Health Supplements"],
                "certifications": [],
                "ratings": 4.0,
                "benefit": "Affordable generic medicines available. Quick prescription processing.",
                "openingHours": {"weekday": "9:00-21:00", "weekend": "10:00-20:00"}
            },
            {
                "id": "h012",
                "name": "HCG Cancer Centre",
                "type": "HOSPITAL",
                "category": "Specialty",
                "speciality": "Oncology",
                "lat": 23.0405,
                "lng": 72.5560,
                "address": "Mithakali, Ahmedabad, Gujarat 380006",
                "contact": "+91-79-66280000",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Bajaj Allianz"],
                "services": ["Medical Oncology", "Radiation Therapy", "Chemotherapy", "PET Scan", "BMT"],
                "certifications": ["NABH"],
                "ratings": 4.6,
                "benefit": "Specialized cancer treatment center. Advanced radiation therapy and bone marrow transplant.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h013",
                "name": "CIMS Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0580,
                "lng": 72.5350,
                "address": "Science City Road, Sola, Ahmedabad, Gujarat",
                "contact": "+91-79-27712771",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Max Bupa"],
                "services": ["Cardiology", "Neurosurgery", "Gastro", "Urology", "Emergency", "ICU"],
                "certifications": ["NABH"],
                "ratings": 4.5,
                "benefit": "Advanced cardiac care with TAVI facility. 300+ bed multi-specialty hospital.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            },
            {
                "id": "h014",
                "name": "Pramukhswami Eye Hospital",
                "type": "HOSPITAL",
                "category": "Specialty",
                "speciality": "Ophthalmology",
                "lat": 23.0480,
                "lng": 72.5450,
                "address": "Paldi, Ahmedabad, Gujarat 380007",
                "contact": "+91-79-26550111",
                "emergency": False,
                "open24x7": False,
                "ayushmanCard": True,
                "maaCard": False,
                "cashlessCompanies": ["Star Health"],
                "services": ["Cataract Surgery", "LASIK", "Glaucoma", "Retina Treatment"],
                "certifications": [],
                "ratings": 4.4,
                "benefit": "Affordable eye care. Ayushman card accepted for cataract and eye surgeries.",
                "openingHours": {"weekday": "9:00-18:00", "weekend": "9:00-13:00"}
            },
            {
                "id": "h015",
                "name": "KD Hospital",
                "type": "HOSPITAL",
                "category": "Multi-Specialty",
                "speciality": "Multispeciality",
                "lat": 23.0600,
                "lng": 72.5680,
                "address": "Vaishnodevi Circle, SG Highway, Ahmedabad",
                "contact": "+91-79-66770000",
                "emergency": True,
                "open24x7": True,
                "ayushmanCard": True,
                "maaCard": True,
                "cashlessCompanies": ["Star Health", "ICICI Lombard", "HDFC Ergo", "Bajaj Allianz"],
                "services": ["All Specialties", "Transplant", "Emergency", "Robotic Surgery", "Rehabilitation"],
                "certifications": ["NABH"],
                "ratings": 4.5,
                "benefit": "State-of-the-art 400-bed hospital. Kidney and liver transplant center.",
                "openingHours": {"weekday": "24/7", "weekend": "24/7"}
            }
        ]

        # Save to location.json for persistence
        self._save_data()

    def _save_data(self):
        """Save facilities data to location.json"""
        try:
            static_json = os.path.join(
                os.path.dirname(__file__), '..', '..', 'frontend', 'static', 'js', 'location.json'
            )
            with open(static_json, 'w') as f:
                json.dump(self.facilities, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save location data: {e}")

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance between two points in km"""
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    @staticmethod
    def estimate_travel_time(distance_km: float, speed_kmh: float = 25) -> int:
        """Estimate travel time in minutes (default urban speed 25 km/h)"""
        if distance_km <= 0:
            return 0
        return max(1, round((distance_km / speed_kmh) * 60))

    @staticmethod
    def get_google_maps_link(lat: float, lng: float, name: str = '') -> str:
        """Generate Google Maps directions URL"""
        import urllib.parse
        encoded_name = urllib.parse.quote(name)
        return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}&destination_place_id={encoded_name}"

    def _enrich_with_distance(self, facility: Dict, user_lat: float, user_lng: float) -> Dict:
        """Add distance and travel time to a facility record"""
        enriched = dict(facility)
        distance = self.haversine_distance(user_lat, user_lng, facility['lat'], facility['lng'])
        enriched['distance'] = distance
        enriched['estimatedTime'] = self.estimate_travel_time(distance)
        enriched['googleMapsLink'] = self.get_google_maps_link(
            facility['lat'], facility['lng'], facility['name']
        )
        return enriched

    def get_all_locations(self, user_lat: Optional[float] = None,
                         user_lng: Optional[float] = None,
                         category: Optional[str] = None) -> List[Dict]:
        """Get all locations, optionally filtered and with distance"""
        results = list(self.facilities)

        # Filter by category
        if category and category.upper() != 'ALL RESOURCES':
            cat_lower = category.lower()
            results = [
                f for f in results
                if (f.get('type', '').lower() == cat_lower or
                    f.get('speciality', '').lower() == cat_lower or
                    f.get('category', '').lower() == cat_lower or
                    cat_lower in f.get('type', '').lower() or
                    cat_lower in f.get('speciality', '').lower())
            ]

        # Add distance info if user location provided
        if user_lat is not None and user_lng is not None:
            results = [self._enrich_with_distance(f, user_lat, user_lng) for f in results]
            results.sort(key=lambda x: x.get('distance', 999))

        return results

    def get_nearby_hospitals(self, user_lat: float, user_lon: float,
                            radius_km: float = 20,
                            speciality: Optional[str] = None,
                            ayushman_only: bool = False,
                            maa_only: bool = False,
                            emergency_only: bool = False) -> List[Dict]:
        """Get hospitals near user within radius"""
        results = []

        for facility in self.facilities:
            if facility.get('type', '').upper() != 'HOSPITAL':
                continue

            distance = self.haversine_distance(user_lat, user_lon, facility['lat'], facility['lng'])
            if distance > radius_km:
                continue

            if speciality and speciality.lower() not in facility.get('speciality', '').lower():
                continue
            if ayushman_only and not facility.get('ayushmanCard', False):
                continue
            if maa_only and not facility.get('maaCard', False):
                continue
            if emergency_only and not facility.get('emergency', False):
                continue

            enriched = self._enrich_with_distance(facility, user_lat, user_lon)
            results.append(enriched)

        results.sort(key=lambda x: x.get('distance', 999))
        return results

    def get_nearby_pharmacies(self, user_lat: float, user_lon: float,
                              radius_km: float = 10,
                              open_now: bool = False) -> List[Dict]:
        """Get pharmacies near user"""
        results = []

        for facility in self.facilities:
            if facility.get('type', '').upper() != 'PHARMACY':
                continue

            distance = self.haversine_distance(user_lat, user_lon, facility['lat'], facility['lng'])
            if distance > radius_km:
                continue

            if open_now and not facility.get('open24x7', False):
                continue

            enriched = self._enrich_with_distance(facility, user_lat, user_lon)
            results.append(enriched)

        results.sort(key=lambda x: x.get('distance', 999))
        return results

    def get_hospital_by_id(self, hospital_id: str) -> Optional[Dict]:
        """Get a specific facility by ID"""
        for facility in self.facilities:
            if facility.get('id') == hospital_id:
                return dict(facility)
        return None

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Public distance calculation"""
        return self.haversine_distance(lat1, lon1, lat2, lon2)

    def search_facilities(self, query: str, facility_type: Optional[str] = None) -> List[Dict]:
        """Full-text search across facility names, specialities, services"""
        query_lower = query.lower()
        results = []

        for facility in self.facilities:
            if facility_type:
                if facility.get('type', '').upper() != facility_type.upper():
                    continue

            searchable = ' '.join([
                facility.get('name', ''),
                facility.get('speciality', ''),
                facility.get('category', ''),
                facility.get('address', ''),
                ' '.join(facility.get('services', [])),
                facility.get('benefit', '')
            ]).lower()

            if query_lower in searchable:
                results.append(dict(facility))

        return results

    def get_emergency_hospitals(self, user_lat: Optional[float] = None,
                                user_lon: Optional[float] = None) -> List[Dict]:
        """Get all emergency hospitals sorted by distance"""
        results = [
            dict(f) for f in self.facilities
            if f.get('emergency', False) and f.get('type', '').upper() == 'HOSPITAL'
        ]

        if user_lat is not None and user_lon is not None:
            results = [self._enrich_with_distance(f, user_lat, user_lon) for f in self.facilities
                       if f.get('emergency', False) and f.get('type', '').upper() == 'HOSPITAL']
            results.sort(key=lambda x: x.get('distance', 999))

        return results

    def get_facilities_with_cards(self, ayushman: bool = False,
                                   maa: bool = False) -> List[Dict]:
        """Get facilities accepting specific government cards"""
        results = []

        for facility in self.facilities:
            if ayushman and facility.get('ayushmanCard', False):
                results.append(dict(facility))
            elif maa and facility.get('maaCard', False):
                results.append(dict(facility))
            elif not ayushman and not maa:
                # Return all with any card
                if facility.get('ayushmanCard', False) or facility.get('maaCard', False):
                    results.append(dict(facility))

        return results
