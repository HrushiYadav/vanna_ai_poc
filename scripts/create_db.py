import sqlite3
import os

# Delete the existing database file if it exists
if os.path.exists('../data/parts.db'):
    os.remove('../data/parts.db')

# Ensure the 'data' directory exists
os.makedirs('../data', exist_ok=True)

# Connect to SQLite (or create it if it doesn't exist)
conn = sqlite3.connect('../data/parts.db')
cursor = conn.cursor()

# Create a table
cursor.execute('''
CREATE TABLE IF NOT EXISTS parts (
    part_id INTEGER PRIMARY KEY,
    part_name TEXT,
    carbon_footprint FLOAT
)
''')

# Insert dummy data
dummy_data = [
    (1, 'Engine Block', 120.5),
    (2, 'Transmission', 95.3),
    (3, 'Battery', 45.0),
    (4, 'Tire', 30.7),
    (5, 'Exhaust System', 60.2)
]
cursor.executemany('INSERT INTO parts (part_id, part_name, carbon_footprint) VALUES (?, ?, ?)', dummy_data)

# Commit and close
conn.commit()
conn.close()

print("Database created and dummy data inserted successfully.")