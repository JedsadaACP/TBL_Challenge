import json
import os
from math import radians, sin, cos, sqrt, atan2
from flask import Flask, jsonify

# --- Data Loading ---

def load_data(filename: str):
    """
    Loads JSON data from a file in the '../data/' directory.
    Assumes this script (app.py) is in the 'backend' directory.
    """
    # Construct the path relative to the current script's directory
    # Current script dir: backend/
    # Target data dir: data/ (which is ../data/ from backend/)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, '..', 'data', filename)
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {data_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {data_path}")
        return None

# Load data at script startup
vehicles_data = load_data('vehicles.json')
shipments_data = load_data('shipments.json')
warehouses_data = load_data('warehouses.json')

if vehicles_data is None or shipments_data is None or warehouses_data is None:
    print("Error: One or more data files could not be loaded. Exiting.")
    # In a real app, you might exit or raise an exception here.
    # For this setup, we'll allow it to continue but data might be missing.

# --- ETA Calculation ---

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Radius of Earth in kilometers

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    a = sin(dLat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dLon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def calculate_eta(vehicle_gps: tuple, warehouse_gps: tuple, average_speed_kmh: float = 60.0) -> float:
    """
    Calculates the Estimated Time of Arrival (ETA) in hours.
    
    :param vehicle_gps: Tuple (latitude, longitude) of the vehicle.
    :param warehouse_gps: Tuple (latitude, longitude) of the warehouse.
    :param average_speed_kmh: Average speed of the vehicle in km/h.
    :return: ETA in hours. Returns -1.0 if GPS data is invalid.
    """
    if not vehicle_gps or not warehouse_gps:
        return -1.0 # Indicate invalid input
    
    # Ensure GPS coordinates are floats
    try:
        v_lat, v_lon = float(vehicle_gps[0]), float(vehicle_gps[1])
        w_lat, w_lon = float(warehouse_gps[0]), float(warehouse_gps[1])
    except (ValueError, TypeError, IndexError):
        print(f"Invalid GPS coordinate format: vehicle_gps={vehicle_gps}, warehouse_gps={warehouse_gps}")
        return -1.0

    distance_km = haversine(v_lat, v_lon, w_lat, w_lon)
    
    if average_speed_kmh <= 0:
        return float('inf') # Avoid division by zero or negative speed
        
    eta_hours = distance_km / average_speed_kmh
    return eta_hours

import copy # For deepcopy

# --- Flask App Setup ---
app = Flask(__name__)

# --- API Endpoints ---

@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    if not vehicles_data or not warehouses_data:
        return jsonify({"error": "Vehicle or warehouse data not loaded"}), 500

    processed_vehicles = []
    vehicles_copy = copy.deepcopy(vehicles_data) # Avoid modifying global data

    for vehicle in vehicles_copy:
        vehicle_gps_coords = vehicle.get('gps_coordinates')
        destination_warehouse_id = vehicle.get('destination')
        
        # Default ETA
        vehicle['eta_hours'] = None

        if vehicle_gps_coords and destination_warehouse_id:
            # Extract vehicle GPS
            v_lat = vehicle_gps_coords.get('latitude')
            v_lon = vehicle_gps_coords.get('longitude')

            if v_lat is not None and v_lon is not None:
                vehicle_gps = (v_lat, v_lon)
                
                # Find destination warehouse
                warehouse = next((wh for wh in warehouses_data if wh.get('warehouse_id') == destination_warehouse_id), None)
                
                if warehouse:
                    warehouse_gps_coords = warehouse.get('location_coordinates')
                    if warehouse_gps_coords:
                        w_lat = warehouse_gps_coords.get('latitude')
                        w_lon = warehouse_gps_coords.get('longitude')
                        
                        if w_lat is not None and w_lon is not None:
                            warehouse_gps = (w_lat, w_lon)
                            eta = calculate_eta(vehicle_gps, warehouse_gps)
                            if eta is not None and eta >= 0:
                                vehicle['eta_hours'] = round(eta, 2)
        processed_vehicles.append(vehicle)
        
    return jsonify(processed_vehicles)

@app.route('/api/warehouses', methods=['GET'])
def get_warehouses():
    if not warehouses_data:
        return jsonify({"error": "Warehouse data not loaded"}), 500
    return jsonify(warehouses_data)

@app.route('/api/warehouses/<string:warehouse_id>/incoming_shipments', methods=['GET'])
def get_incoming_shipments(warehouse_id):
    if not warehouses_data or not vehicles_data or not shipments_data:
        return jsonify({"error": "Core data not loaded"}), 500

    target_warehouse = next((wh for wh in warehouses_data if wh.get('warehouse_id') == warehouse_id), None)
    if not target_warehouse:
        return jsonify({"error": "Warehouse not found"}), 404

    warehouse_gps_coords = target_warehouse.get('location_coordinates')
    if not warehouse_gps_coords or warehouse_gps_coords.get('latitude') is None or warehouse_gps_coords.get('longitude') is None:
        return jsonify({"error": "Warehouse location coordinates missing or invalid"}), 500
        
    w_lat = warehouse_gps_coords['latitude']
    w_lon = warehouse_gps_coords['longitude']
    warehouse_gps = (w_lat, w_lon)

    incoming_shipments_details = []

    for vehicle in vehicles_data:
        if vehicle.get('destination') == warehouse_id:
            vehicle_copy = copy.deepcopy(vehicle)
            
            # Calculate ETA for this vehicle to the target warehouse
            vehicle_gps_coords = vehicle_copy.get('gps_coordinates')
            eta = None
            if vehicle_gps_coords and vehicle_gps_coords.get('latitude') is not None and vehicle_gps_coords.get('longitude') is not None:
                v_lat = vehicle_gps_coords['latitude']
                v_lon = vehicle_gps_coords['longitude']
                calculated_eta = calculate_eta((v_lat, v_lon), warehouse_gps)
                if calculated_eta is not None and calculated_eta >=0:
                    eta = round(calculated_eta, 2)
            
            vehicle_copy['eta_hours'] = eta

            # Find corresponding shipment
            shipment = next((s for s in shipments_data if s.get('vehicle_registration_number') == vehicle_copy.get('registration_number')), None)
            
            if shipment:
                vehicle_copy['sku_details'] = shipment.get('sku_details', [])
                vehicle_copy['scheduled_arrival_time'] = shipment.get('scheduled_arrival_time')
            else:
                vehicle_copy['sku_details'] = []
                vehicle_copy['scheduled_arrival_time'] = None
                
            incoming_shipments_details.append(vehicle_copy)

    # Sort by ETA (handle None ETAs by placing them at the end or beginning based on preference)
    incoming_shipments_details.sort(key=lambda x: (x['eta_hours'] is None, x['eta_hours']))

    return jsonify(incoming_shipments_details)


if __name__ == '__main__':
    # Basic check if data loaded
    if vehicles_data is None or shipments_data is None or warehouses_data is None:
        print("Warning: One or more data files could not be loaded. API might not function correctly.")
    
    # Example usage of ETA calculation (can be removed later)
    # This is just for testing the ETA function during development.
    if vehicles_data and warehouses_data and len(vehicles_data) > 0 and len(warehouses_data) > 0:
        try:
            sample_vehicle_gps_coords = vehicles_data[0].get('gps_coordinates',{})
            sample_vehicle_gps = (sample_vehicle_gps_coords.get('latitude'), sample_vehicle_gps_coords.get('longitude'))
            
            sample_warehouse_gps_coords = warehouses_data[0].get('location_coordinates',{})
            sample_warehouse_gps = (sample_warehouse_gps_coords.get('latitude'), sample_warehouse_gps_coords.get('longitude'))

            if all(sample_vehicle_gps) and all(sample_warehouse_gps) :
                eta = calculate_eta(sample_vehicle_gps, sample_warehouse_gps)
                if eta is not None and eta >= 0:
                    print(f"Sample ETA Calculation:")
                    print(f"  Vehicle GPS: {sample_vehicle_gps}")
                    print(f"  Warehouse GPS: {sample_warehouse_gps}")
                    print(f"  Calculated ETA: {eta:.2f} hours")
                else:
                    print(f"Could not calculate sample ETA due to invalid GPS data or other issues.")
            else:
                print("Sample vehicle or warehouse missing GPS data for ETA calculation test.")

        except (IndexError, KeyError, TypeError) as e:
            print(f"Error accessing sample data for ETA calculation: {e}")
            print("Make sure your vehicles.json and warehouses.json have at least one entry with GPS coordinates.")
    else:
        print("Not enough data to perform sample ETA calculation printout.")

    app.run(debug=True, host='0.0.0.0', port=5000)
