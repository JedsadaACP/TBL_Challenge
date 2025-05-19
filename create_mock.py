import random
from datetime import datetime, timedelta
import json
import csv

# ----------------------
# Helper Functions
# ----------------------

def random_lat(base=13.7465):
    return round(base + random.uniform(-0.02, 0.02), 6)

def random_lon(base=100.5278):
    return round(base + random.uniform(-0.02, 0.02), 6)

def random_time_offset():
    return datetime.now() - timedelta(minutes=random.randint(0, 30))

def is_near_location(current_coords, target_coords, threshold_km=1.0):
    distance_km = ((current_coords[0] - target_coords[0])**2 + (current_coords[1] - target_coords[1])**2)**0.5 * 100
    return distance_km < threshold_km

def calculate_status(truck, locations):
    if truck["speed_kmh"] == 0:
        time_diff = (datetime.now() - datetime.fromisoformat(truck["last_updated"])).total_seconds() / 60
        if time_diff > 10:
            return "delayed"
        elif is_near_location((truck["latitude"], truck["longitude"]), locations[truck["origin"]]):
            return "loading" if truck["direction"] == "outbound" else "unloading"
        else:
            return "stopped"
    elif is_near_location((truck["latitude"], truck["longitude"]), locations[truck["destination"]]):
        return "arrived"
    else:
        return "en_route"

def calculate_eta(current_coords, destination_coords, speed_kmh):
    if speed_kmh <= 0:
        return None
    distance_km = ((current_coords[0] - destination_coords[0])**2 + (current_coords[1] - destination_coords[1])**2)**0.5 * 100
    hours = distance_km / speed_kmh
    eta = datetime.now() + timedelta(hours=hours)
    return eta.isoformat()

# ----------------------
# Fixed Locations
# ----------------------

locations = {
    "Factory": (13.7465, 100.5278),
    "Warehouse": (13.7665, 100.5278)
}

# ----------------------
# Truck Definitions (4 Trucks)
# ----------------------

trucks = [
    {"id": "TRK101", "business_unit": "TBL", "direction": "outbound"},
    {"id": "TRK102", "business_unit": "TBL", "direction": "inbound"},
    {"id": "TRK103", "business_unit": "Sermsuk", "direction": "outbound"},
    {"id": "TRK104", "business_unit": "Sermsuk", "direction": "inbound"}
]

# ----------------------
# Generate Control Tower Data (JSON)
# ----------------------

json_data = []
for truck in trucks:
    origin, destination = ("Factory", "Warehouse") if truck["direction"] == "outbound" else ("Warehouse", "Factory")
    origin_coords = locations[origin]
    dest_coords = locations[destination]
    
    lat = origin_coords[0] + (dest_coords[0] - origin_coords[0]) * random.uniform(0.3, 0.7)
    lon = origin_coords[1] + (dest_coords[1] - origin_coords[1]) * random.uniform(0.3, 0.7)
    
    speed = random.randint(0, 80)
    last_updated = random_time_offset().isoformat()
    
    truck_data = {
        "truck_id": truck["id"],
        "business_unit": truck["business_unit"],
        "latitude": round(lat + random.uniform(-0.001, 0.001), 6),
        "longitude": round(lon + random.uniform(-0.001, 0.001), 6),
        "speed_kmh": speed,
        "origin": origin,
        "destination": destination,
        "last_updated": last_updated,
        "status": None,
        "direction": None,
        "eta": None
    }
    
    # Calculate status, direction, eta
    truck_data["status"] = calculate_status(truck_data, locations)
    truck_data["direction"] = "outbound" if origin == "Factory" else "inbound"
    truck_data["eta"] = calculate_eta((lat, lon), locations[destination], speed)
    
    json_data.append(truck_data)

# Save to JSON
with open("mock_data/control_tower.json", "w") as f:
    json.dump(json_data, f, indent=2)

print("✅ Generated control_tower.json")

# ----------------------
# Generate ASN Shipment Data with order_id (CSV)
# ----------------------

shipment_csv_headers = ["order_id", "truck_id", "sku", "quantity", "expected_arrival_time"]

with open("mock_data/shipment_data.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=shipment_csv_headers)
    writer.writeheader()
    
    # Only outbound trucks have shipment data
    for truck in trucks:
        if truck["direction"] == "outbound":
            num_items = random.randint(1, 2)
            for _ in range(num_items):
                writer.writerow({
                    "order_id": f"ORD{random.randint(100, 999)}",  # Generate unique order ID
                    "truck_id": truck["id"],
                    "sku": random.choice(["SKU001", "SKU002", "SKU003"]),
                    "quantity": random.randint(100, 300),
                    "expected_arrival_time": (datetime.now() + timedelta(hours=random.randint(1, 3))).isoformat()
                })
        else:
            continue

print("📦 Generated shipment_data.csv with order_id")