import json
import csv
import sqlite3
from datetime import datetime

# ----------------------
# Step 1: Load Truck Data
# ----------------------

def load_truck_data():
    """Load truck data from mock JSON file"""
    with open("mock_data/control_tower.json", "r") as f:
        data = json.load(f)
    return data

# ----------------------
# Step 2: Load Shipment Data
# ----------------------

def load_shipment_data():
    """Load shipment data from CSV file"""
    shipments = []
    with open("mock_data/shipment_data.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            shipments.append(row)
    return shipments

# ----------------------
# Step 3: Merge Truck + Shipment Data
# ----------------------

def merge_data(truck_data, shipment_data):
    """Merge shipment data into truck records using truck_id"""
    for truck in truck_data:
        # Filter shipments for this truck
        truck["shipments"] = [s for s in shipment_data if s["truck_id"] == truck["truck_id"]]
    return truck_data

# ----------------------
# Step 4: Save to Central Database
# ----------------------

def save_to_db(data):
    """Save merged truck data into SQLite database"""
    conn = sqlite3.connect("tracking.db")
    c = conn.cursor()

    # Drop tables if they exist (to reset schema)
    c.execute("DROP TABLE IF EXISTS deliveries")
    c.execute("DROP TABLE IF EXISTS shipments")

    # Create tables
    c.execute('''
        CREATE TABLE deliveries (
            truck_id TEXT PRIMARY KEY,
            business_unit TEXT,
            latitude REAL,
            longitude REAL,
            speed_kmh INTEGER,
            status TEXT,
            direction TEXT,
            origin TEXT,
            destination TEXT,
            last_updated TEXT,
            eta TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE shipments (
            order_id TEXT,
            truck_id TEXT,
            sku TEXT,
            quantity INTEGER,
            expected_arrival_time TEXT,
            FOREIGN KEY(truck_id) REFERENCES deliveries(truck_id)
        )
    ''')

    # Insert deliveries
    for truck in data:
        c.execute('''
            INSERT INTO deliveries 
            (truck_id, business_unit, latitude, longitude, speed_kmh, status, direction, origin, destination, last_updated, eta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            truck["truck_id"],
            truck["business_unit"],
            truck["latitude"],
            truck["longitude"],
            truck["speed_kmh"],
            truck["status"],
            truck["direction"],
            truck["origin"],
            truck["destination"],
            truck["last_updated"],
            truck["eta"]
        ))

        # Insert shipments
        for shipment in truck["shipments"]:
            c.execute('''
                INSERT INTO shipments 
                (order_id, truck_id, sku, quantity, expected_arrival_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                shipment["order_id"],
                truck["truck_id"],
                shipment["sku"],
                shipment["quantity"],
                shipment["expected_arrival_time"]
            ))

    conn.commit()
    conn.close()
    print("💾 Merged data saved to tracking.db")
    
    # ----------------------
# Run ETL Pipeline
# ----------------------

if __name__ == "__main__":
    truck_data = load_truck_data()
    shipment_data = load_shipment_data()
    merged_data = merge_data(truck_data, shipment_data)
    
    save_to_db(merged_data)