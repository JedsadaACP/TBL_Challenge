import json
from datetime import datetime, timedelta
import random

# --- Sample Data Definitions ---

# Warehouses
warehouses_data = [
    {
        "warehouse_id": "WH-BKK-01",
        "name": "Bangkok Central Warehouse",
        "location_coordinates": {"latitude": 13.7563, "longitude": 100.5018}, # Bangkok
        "geofence_radius_km": 5.0
    },
    {
        "warehouse_id": "WH-NKR-02",
        "name": "Nakhon Ratchasima Hub",
        "location_coordinates": {"latitude": 14.9723, "longitude": 102.0856}, # Nakhon Ratchasima
        "geofence_radius_km": 7.5
    },
    {
        "warehouse_id": "WH-CNX-03",
        "name": "Chiang Mai Distribution Point",
        "location_coordinates": {"latitude": 18.7877, "longitude": 98.9931}, # Chiang Mai
        "geofence_radius_km": 6.0
    }
]

# Vehicles
vehicles_data = [
    {
        "registration_number": "VEH-001-AB",
        "gps_coordinates": {"latitude": 14.0123, "longitude": 100.6045}, # Near Sermsuk Factory
        "speed": 65.5,
        "last_update_timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z",
        "origin": "Sermsuk Factory (Pathum Thani)",
        "destination": "WH-BKK-01", # Bangkok Central Warehouse
        "business_unit": "Beverages",
        "status": "In Transit"
    },
    {
        "registration_number": "VEH-002-CD",
        "gps_coordinates": {"latitude": 16.4567, "longitude": 99.5123}, # Near TBL Factory
        "speed": 72.0,
        "last_update_timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat() + "Z",
        "origin": "TBL Factory (Kamphaeng Phet)",
        "destination": "WH-NKR-02", # Nakhon Ratchasima Hub
        "business_unit": "Snacks",
        "status": "Loading"
    },
    {
        "registration_number": "VEH-003-EF",
        "gps_coordinates": {"latitude": 13.7800, "longitude": 100.5200}, # Approaching Bangkok
        "speed": 45.0,
        "last_update_timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z",
        "origin": "Sermsuk Factory (Pathum Thani)",
        "destination": "WH-BKK-01", # Bangkok Central Warehouse
        "business_unit": "Beverages",
        "status": "Delayed"
    },
    {
        "registration_number": "VEH-004-GH",
        "gps_coordinates": {"latitude": 15.0100, "longitude": 102.0100}, # Near Nakhon Ratchasima
        "speed": 78.5,
        "last_update_timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat() + "Z",
        "origin": "TBL Factory (Kamphaeng Phet)",
        "destination": "WH-CNX-03", # Chiang Mai Distribution Point
        "business_unit": "Water",
        "status": "In Transit"
    }
]

# Shipments
shipments_data = [
    {
        "vehicle_registration_number": "VEH-001-AB",
        "sku_details": [
            {"sku_id": "BEV001", "description": "Chang Beer Can 320ml", "quantity": 1200},
            {"sku_id": "BEV002", "description": "Leo Beer Bottle 620ml", "quantity": 800}
        ],
        "scheduled_arrival_time": (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z",
        "destination_warehouse_id": "WH-BKK-01"
    },
    {
        "vehicle_registration_number": "VEH-002-CD", # Currently "Loading"
        "sku_details": [
            {"sku_id": "SNK001", "description": "Lay's Classic Potato Chips 50g", "quantity": 2000},
            {"sku_id": "SNK002", "description": "Tasto Crab Curry Flavor 48g", "quantity": 1500}
        ],
        "scheduled_arrival_time": (datetime.utcnow() + timedelta(hours=8)).isoformat() + "Z",
        "destination_warehouse_id": "WH-NKR-02"
    },
    {
        "vehicle_registration_number": "VEH-003-EF", # "Delayed"
        "sku_details": [
            {"sku_id": "WAT001", "description": "Singha Drinking Water 600ml", "quantity": 2400},
            {"sku_id": "WAT002", "description": "Crystal Water Bottle 600ml", "quantity": 1800}
        ],
        "scheduled_arrival_time": (datetime.utcnow() + timedelta(hours=1, minutes=30)).isoformat() + "Z",
        "destination_warehouse_id": "WH-BKK-01"
    },
    {
        "vehicle_registration_number": "VEH-004-GH",
        "sku_details": [
            {"sku_id": "WAT003", "description": "Nestle Pure Life 1.5L", "quantity": 1000},
            {"sku_id": "BEV003", "description": "Oishi Green Tea Honey Lemon 380ml", "quantity": 700}
        ],
        "scheduled_arrival_time": (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z",
        "destination_warehouse_id": "WH-CNX-03"
    }
]

# --- Main script logic to write data to JSON files ---
def generate_data():
    """Generates mock data and writes it to JSON files."""
    with open('data/warehouses.json', 'w') as f:
        json.dump(warehouses_data, f, indent=4)
    print("Successfully generated data/warehouses.json")

    with open('data/vehicles.json', 'w') as f:
        json.dump(vehicles_data, f, indent=4)
    print("Successfully generated data/vehicles.json")

    with open('data/shipments.json', 'w') as f:
        json.dump(shipments_data, f, indent=4)
    print("Successfully generated data/shipments.json")

if __name__ == "__main__":
    generate_data()
