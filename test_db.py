import sqlite3

conn = sqlite3.connect("tracking.db")
c = conn.cursor()

# Get all trucks
c.execute("SELECT * FROM deliveries")
trucks = c.fetchall()
print("🚛 Trucks in DB:")
for t in trucks:
    print(t)

# Get all shipments
c.execute("SELECT * FROM shipments")
shipments = c.fetchall()
print("\n📦 Shipments in DB:")
for s in shipments:
    print(s)

conn.close()