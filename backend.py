from flask import Flask, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False  # Keep JSON order consistent

# ----------------------
# Helper: Get Database Connection
# ----------------------

def get_db_connection():
    conn = sqlite3.connect("tracking.db")
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

# ----------------------
# API Endpoint: Get Dashboard Data
# ----------------------

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    conn = get_db_connection()
    c = conn.cursor()

    # Get all trucks
    c.execute("SELECT * FROM deliveries")
    trucks = [dict(row) for row in c.fetchall()]

    # Get all shipments
    c.execute("SELECT * FROM shipments")
    shipments = [dict(row) for row in c.fetchall()]

    conn.close()

    # Merge shipments into truck data
    for truck in trucks:
        truck_shipments = [s for s in shipments if s["truck_id"] == truck["truck_id"]]
        truck["shipments"] = truck_shipments
        
        # Add is_delayed flag if truck has shipments
        if truck_shipments:
            truck["is_delayed"] = any(
                datetime.fromisoformat(truck["eta"]) > datetime.fromisoformat(s["expected_arrival_time"])
                for s in truck_shipments if s["expected_arrival_time"]
            )
        else:
            truck["is_delayed"] = False

    return jsonify(trucks)

# ----------------------
# Health Check Endpoint
# ----------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

# ----------------------
# Run the Server
# ----------------------

if __name__ == "__main__":
    print("🔌 Starting backend API...")
    app.run(debug=True, host="0.0.0.0", port=5000)