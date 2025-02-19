import os
import sqlite3
import re
import numpy as np
import pandas as pd
from flask import Flask, jsonify, Response, request
from vanna.openai import OpenAI_Chat
from openai import AzureOpenAI
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)

        OpenAI_Chat.__init__(self, client=AzureOpenAI(
            azure_endpoint="",
            api_key="",
            api_version=""
        ), config=config)

vn = MyVanna(config={'model': ''})

vn.connect_to_sqlite('carbon_footprint.db')

df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
for ddl in df_ddl['sql'].to_list():
    vn.train(ddl=ddl)

vn.train(ddl="""
    CREATE TABLE IF NOT EXISTS batteries (
        id INTEGER PRIMARY KEY,
        part_number TEXT UNIQUE,
        type TEXT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
""")

vn.train(documentation="Battery carbon footprint is measured in kg CO2e based on the lifecycle emissions.")

vn.train(sql="SELECT * FROM batteries WHERE capacity_kwh > 100")
vn.train(sql="SELECT part_number, type FROM batteries WHERE carbon_footprint_kg < 5000")
vn.train(sql="SELECT AVG(capacity_kwh) FROM batteries WHERE type = 'Type-1'")
vn.train(sql="SELECT COUNT(*) FROM batteries WHERE type = 'Type-3' AND capacity_kwh > 120")


training_data = vn.get_training_data()
print(vn.get_training_data())

def populate_dummy_data():
    """Creates a SQLite table and inserts sample battery data."""
    conn = sqlite3.connect('carbon_footprint.db')
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS batteries")

    cursor.execute('''
    CREATE TABLE batteries (
        id INTEGER PRIMARY KEY,
        part_number TEXT UNIQUE,
        type TEXT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
    ''')

    dummy_data = [
        (f'PART-{i}', f'Type-{i % 5}', round(np.random.uniform(50, 150), 2), round(np.random.uniform(5000, 15000), 2))
        for i in range(1, 51)
    ]

    cursor.executemany(
        'INSERT INTO batteries (part_number, type, capacity_kwh, carbon_footprint_kg) VALUES (?, ?, ?, ?)',
        dummy_data
    )

    conn.commit()
    conn.close()
    print("✅ Dummy data inserted into `batteries` table!")

app = VannaFlaskApp(vn)

if __name__ == "__main__":
    populate_dummy_data()  
    app.run()
