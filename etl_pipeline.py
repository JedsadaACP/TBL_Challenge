# TBL_CHALLENGE/etl_pipeline.py
import sqlite3
import json
import csv
from datetime import datetime

DATABASE_PATH = 'database/tracking.db'
CONTROL_TOWER_DATA_PATH = 'mock_data/control_tower.json'
SHIPMENT_DATA_PATH = 'mock_data/shipment_data.csv'

def create_tables(conn):
    """Creates the necessary tables in the SQLite database if they don't exist."""
    cursor = conn.cursor()
    
    # Trucks table: Stores information primarily from the control tower
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trucks (
            truck_id TEXT PRIMARY KEY,
            business_unit TEXT,
            current_latitude REAL,
            current_longitude REAL,
            current_speed_kmh INTEGER,
            last_updated_gps TEXT,         -- From control_tower.json: last_updated
            current_origin TEXT,           -- From control_tower.json: origin
            current_destination TEXT,      -- From control_tower.json: destination
            direction TEXT,                -- From control_tower.json: direction (outbound/inbound)
            status TEXT,                   -- From control_tower.json: status (en_route, arrived, etc.)
            calculated_eta_ct TEXT,      -- From control_tower.json: eta (ETA calculated by control tower)
            is_delayed BOOLEAN DEFAULT FALSE -- Will be updated by backend based on comparison
        )
    ''')
    
    # Shipments table: Stores ASN data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,          -- From shipment_data.csv
            truck_id TEXT,                 -- From shipment_data.csv
            sku TEXT,                      -- From shipment_data.csv
            quantity INTEGER,              -- From shipment_data.csv
            expected_arrival_time_asn TEXT, -- From shipment_data.csv: expected_arrival_time
            FOREIGN KEY (truck_id) REFERENCES trucks (truck_id)
        )
    ''')
    conn.commit()
    print("📄 Tables ensured in database.")

def clear_data(conn):
    """Clears all data from the tables for a fresh load."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shipments")
    cursor.execute("DELETE FROM trucks")
    conn.commit()
    print("🗑️  Existing data cleared from tables.")

def load_control_tower_data(conn):
    """Loads data from control_tower.json into the trucks table."""
    cursor = conn.cursor()
    try:
        with open(CONTROL_TOWER_DATA_PATH, 'r', encoding='utf-8') as f:
            control_tower_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: {CONTROL_TOWER_DATA_PATH} not found.")
        return 0
    except json.JSONDecodeError:
        print(f"❌ ERROR: Could not decode JSON from {CONTROL_TOWER_DATA_PATH}.")
        return 0

    trucks_loaded_count = 0
    for truck_data in control_tower_data:
        try:
            cursor.execute('''
                INSERT INTO trucks (
                    truck_id, business_unit, current_latitude, current_longitude,
                    current_speed_kmh, last_updated_gps, current_origin, current_destination,
                    direction, status, calculated_eta_ct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                truck_data['truck_id'],
                truck_data['business_unit'],
                truck_data['latitude'],
                truck_data['longitude'],
                truck_data['speed_kmh'],
                truck_data['last_updated'], # Renamed in DB for clarity
                truck_data['origin'],
                truck_data['destination'],
                truck_data['direction'],
                truck_data['status'],
                truck_data['eta'] # Renamed in DB for clarity
            ))
            trucks_loaded_count += 1
        except sqlite3.IntegrityError as e:
            print(f"⚠️  Warning: Could not insert truck {truck_data.get('truck_id', 'N/A')}. Error: {e}. Skipping.")
        except KeyError as e:
            print(f"⚠️  Warning: Missing key {e} in truck data: {truck_data}. Skipping.")
            
    conn.commit()
    print(f"🚚 Loaded {trucks_loaded_count} truck records from Control Tower data.")
    return trucks_loaded_count

def load_shipment_data(conn):
    """Loads data from shipment_data.csv into the shipments table."""
    cursor = conn.cursor()
    try:
        with open(SHIPMENT_DATA_PATH, 'r', encoding='utf-8-sig') as f: # utf-8-sig for potential BOM
            reader = csv.DictReader(f)
            shipments_data = list(reader)
    except FileNotFoundError:
        print(f"❌ ERROR: {SHIPMENT_DATA_PATH} not found.")
        return 0
    except Exception as e:
        print(f"❌ ERROR reading {SHIPMENT_DATA_PATH}: {e}")
        return 0

    shipments_loaded_count = 0
    for row_num, shipment_data in enumerate(shipments_data, 1):
        try:
            # Ensure all required keys exist, matching your CSV headers
            truck_id = shipment_data['truck_id']
            order_id = shipment_data['order_id']
            sku = shipment_data['sku']
            quantity = int(shipment_data['quantity'])
            expected_arrival_time = shipment_data['expected_arrival_time']

            cursor.execute('''
                INSERT INTO shipments (
                    order_id, truck_id, sku, quantity, expected_arrival_time_asn
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                order_id,
                truck_id,
                sku,
                quantity,
                expected_arrival_time # Renamed in DB for clarity
            ))
            shipments_loaded_count += 1
        except sqlite3.IntegrityError as e:
            print(f"⚠️  Warning: Could not insert shipment for order {shipment_data.get('order_id', 'N/A')} (row {row_num}). Error: {e}. Might be duplicate order_id. Skipping.")
        except KeyError as e:
            print(f"⚠️  Warning: Missing key {e} in shipment CSV row {row_num}: {shipment_data}. Skipping.")
        except ValueError as e:
            print(f"⚠️  Warning: Data type error in shipment CSV row {row_num} (e.g., quantity not an int): {e}. Row: {shipment_data}. Skipping.")

    conn.commit()
    print(f"📦 Loaded {shipments_loaded_count} shipment records from ASN data.")
    return shipments_loaded_count

def main():
    print("🚀 Starting ETL Pipeline...")
    
    # Ensure database directory exists (optional, good practice)
    import os
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    create_tables(conn)
    clear_data(conn) # Clear data before loading new mock data
    
    control_tower_success = load_control_tower_data(conn)
    shipment_success = load_shipment_data(conn)
    
    conn.close()
    
    if control_tower_success > 0 or shipment_success > 0:
        print("✅ ETL Pipeline completed successfully.")
    else:
        print("⚠️  ETL Pipeline completed, but no new data was loaded. Check source files or logs.")

if __name__ == '__main__':
    main()