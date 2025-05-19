# TBL_CHALLENGE/backend.py
import sqlite3
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import random
import time # For simulating delays

DATABASE_PATH = 'database/tracking.db'
SIMULATION_INTERVAL_SECONDS = 10 # How often to simulate truck movement updates
WAREHOUSE_COORDS = (13.7665, 100.5278) # From your create_mock.py
FACTORY_COORDS = (13.7465, 100.5278)   # From your create_mock.py

app = Flask(__name__)
CORS(app) # Enable CORS for local development

# --- Database Helper ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

# --- Data Fetching and Processing Logic ---
def fetch_all_truck_data():
    """Fetches all truck data and their associated shipments, then processes it."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all trucks
    cursor.execute("SELECT * FROM trucks")
    trucks_db = cursor.fetchall()

    processed_trucks = []
    for truck_row in trucks_db:
        truck = dict(truck_row) # Convert sqlite3.Row to dict

        # Fetch shipments for this truck
        cursor.execute("SELECT * FROM shipments WHERE truck_id = ?", (truck['truck_id'],))
        shipments_db = cursor.fetchall()
        truck['shipments'] = [dict(shipment) for shipment in shipments_db]

        # --- Real-time Simulation (for demo) ---
        # In a real system, this data would come from live GPS updates.
        # Here, we simulate movement if the truck is 'en_route'.
        if truck.get('status') == 'en_route' and truck.get('current_speed_kmh', 0) > 0:
            # Simulate small GPS change
            truck['current_latitude'] += random.uniform(-0.0005, 0.0005)
            truck['current_longitude'] += random.uniform(-0.0005, 0.0005)
            
            # Simulate ETA recalculation (very basic: reduce ETA slightly if moving)
            # A more robust ETA would use a routing service or more complex calculation.
            if truck.get('calculated_eta_ct'):
                try:
                    current_eta_dt = datetime.datetime.fromisoformat(truck['calculated_eta_ct'])
                    # Reduce ETA by a small amount, but don't let it go past now easily
                    reduction_seconds = random.randint(SIMULATION_INTERVAL_SECONDS - 5, SIMULATION_INTERVAL_SECONDS + 5)
                    new_eta_dt = current_eta_dt - datetime.timedelta(seconds=reduction_seconds)
                    
                    # Ensure ETA doesn't become in the past unless very close to arrival
                    # For simplicity, we'll just update it. A real system needs checks.
                    truck['calculated_eta_ct'] = new_eta_dt.isoformat()
                except ValueError:
                    pass # Ignore if ETA is not a valid ISO format

        truck['last_updated_gps'] = datetime.datetime.utcnow().isoformat() + "Z" # Simulate fresh update

        # --- Calculate Delay Status ---
        # is_delayed should be True if calculated_eta_ct is later than ANY shipment's expected_arrival_time_asn
        truck['is_delayed'] = False # Default
        if truck.get('calculated_eta_ct') and truck['shipments']:
            try:
                eta_ct_dt = datetime.datetime.fromisoformat(truck['calculated_eta_ct'].replace("Z", ""))
                for shipment in truck['shipments']:
                    if shipment.get('expected_arrival_time_asn'):
                        try:
                            expected_asn_dt = datetime.datetime.fromisoformat(shipment['expected_arrival_time_asn'].replace("Z", ""))
                            if eta_ct_dt > expected_asn_dt:
                                truck['is_delayed'] = True
                                break # One delayed shipment makes the truck delayed
                        except ValueError:
                            print(f"Warning: Could not parse expected_arrival_time_asn for shipment {shipment.get('order_id')}")
            except ValueError:
                 print(f"Warning: Could not parse calculated_eta_ct for truck {truck.get('truck_id')}")


        # Rename fields to match frontend expectations (from your initial mock data structure)
        # This helps if the frontend was built based on that initial structure.
        # If frontend is flexible, this mapping can be simpler.
        frontend_truck = {
            "truck_id": truck.get('truck_id'),
            "business_unit": truck.get('business_unit'),
            "latitude": truck.get('current_latitude'),
            "longitude": truck.get('current_longitude'),
            "speed_kmh": truck.get('current_speed_kmh'),
            "last_updated": truck.get('last_updated_gps'),
            "origin": truck.get('current_origin'),
            "destination": truck.get('current_destination'),
            "direction": truck.get('direction'),
            "status": truck.get('status'),
            "eta": truck.get('calculated_eta_ct'), # Frontend expects 'eta'
            "is_delayed": truck.get('is_delayed'),
            "shipments": []
        }

        for shipment_db in truck['shipments']:
            frontend_truck['shipments'].append({
                "order_id": shipment_db.get('order_id'),
                "sku": shipment_db.get('sku'),
                "quantity": shipment_db.get('quantity'),
                # Frontend expects 'expected_arrival_time'
                "expected_arrival_time": shipment_db.get('expected_arrival_time_asn'),
                "truck_id": shipment_db.get('truck_id') # Already present, but good to be explicit
            })
        
        processed_trucks.append(frontend_truck)

    conn.close()
    return processed_trucks

# --- API Endpoints ---
@app.route('/api/trucks', methods=['GET'])
def get_trucks():
    """
    Endpoint to get all truck data with simulated updates.
    This simulates the "real-time" aspect.
    """
    trucks_data = fetch_all_truck_data()
    return jsonify(trucks_data)

@app.route('/api/warehouse-location', methods=['GET'])
def get_warehouse_location():
    return jsonify({"latitude": WAREHOUSE_COORDS[0], "longitude": WAREHOUSE_COORDS[1], "name": "Main Warehouse"})

@app.route('/api/factory-location', methods=['GET'])
def get_factory_location():
    return jsonify({"latitude": FACTORY_COORDS[0], "longitude": FACTORY_COORDS[1], "name": "Main Factory"})

# --- Main Application Runner ---
if __name__ == '__main__':
    print(f"🚀 Backend server starting...")
    print(f"Database Path: {DATABASE_PATH}")
    print(f"Warehouse Coords: {WAREHOUSE_COORDS}")
    print(f"Factory Coords: {FACTORY_COORDS}")
    print(f"Simulating truck updates roughly every {SIMULATION_INTERVAL_SECONDS} seconds on API call.")
    # For a hackathon, debug=True is fine. For production, use a proper WSGI server.
    app.run(debug=True, port=5001, use_reloader=False) # use_reloader=False if issues with threads/db