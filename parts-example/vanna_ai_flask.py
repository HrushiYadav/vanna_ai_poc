import os
import sqlite3
import re
import numpy as np
import pandas as pd
from flask import Flask, jsonify, Response, request
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp
from openai import OpenAI
import random

class LLMStudioVanna(ChromaDB_VectorStore):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        self.config = config or {}
        self.model = self.config.get('model', 'Mistral-Nemo-Instruct-2407')
        
        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="sk-no-key-needed"  
        )
    
    def system_message(self, message):
        """Format a system message for the LLM"""
        return {"role": "system", "content": message}
    
    def user_message(self, message):
        """Format a user message for the LLM"""
        return {"role": "user", "content": message}
    
    def assistant_message(self, message):
        """Format an assistant message for the LLM"""
        return {"role": "assistant", "content": message}
    
    def submit_prompt(self, messages, model=None, temperature=0.0, max_tokens=4000):
        """Submit a prompt to the LLM Studio API"""
        model = model or self.model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error with LLM Studio API: {e}")
            return "I couldn't process that request. Please check your LLM Studio server connection."

vn = LLMStudioVanna(config={'model': 'Mistral-Nemo-Instruct-2407'})

client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="sk-no-key-needed")
print(client.models.list())

vn.connect_to_sqlite('carbon_footprint.db')

try:
    df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
    for ddl in df_ddl['sql'].to_list():
        vn.train(ddl=ddl)
except Exception as e:
    print(f"Error fetching schema: {e}. Will continue with manual training.")

vn.train(ddl="""
    CREATE TABLE IF NOT EXISTS batteries (
        id INTEGER PRIMARY KEY,
        part_number TEXT UNIQUE,
        manufacturer TEXT,
        distributor TEXT,
        size TEXT,
        connector_length FLOAT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
""")

vn.train(documentation="Battery specifications include part numbers, manufacturers, distributors, size, connector length, capacity, and carbon footprint in kg CO2e.")

vn.train(sql="SELECT * FROM batteries WHERE capacity_kwh > 100")
vn.train(sql="SELECT part_number, manufacturer FROM batteries WHERE carbon_footprint_kg < 5000")
vn.train(sql="SELECT AVG(capacity_kwh) FROM batteries WHERE manufacturer = 'Tesla'")
vn.train(sql="SELECT COUNT(*) FROM batteries WHERE distributor = 'Digi-Key' AND size = 'Large'")

def populate_dummy_data():
    """Creates a SQLite table and inserts sample battery data."""
    conn = sqlite3.connect('carbon_footprint.db')
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS batteries")
    
    cursor.execute('''
    CREATE TABLE batteries (
        id INTEGER PRIMARY KEY,
        part_number TEXT UNIQUE,
        manufacturer TEXT,
        distributor TEXT,
        size TEXT,
        connector_length FLOAT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
    ''')

    manufacturers = ["Tesla", "Panasonic", "LG Energy", "Samsung SDI", "CATL"]
    distributors = ["Digi-Key", "Mouser", "Arrow Electronics", "Avnet", "RS Components"]
    sizes = ["Small", "Medium", "Large"]

    dummy_data = [
        (
            f"BAT-{random.randint(1000, 9999)}",  
            random.choice(manufacturers),       
            random.choice(distributors),      
            random.choice(sizes),              
            round(np.random.uniform(0.5, 5.0), 2),  
            round(np.random.uniform(50, 150), 2),  
            round(np.random.uniform(5000, 15000), 2)  
        )
        for _ in range(50)
    ]

    cursor.executemany(
        'INSERT INTO batteries (part_number, manufacturer, distributor, size, connector_length, capacity_kwh, carbon_footprint_kg) VALUES (?, ?, ?, ?, ?, ?, ?)',
        dummy_data
    )

    conn.commit()
    conn.close()
    print("✅ Dummy data inserted into `batteries` table!")

app = VannaFlaskApp(vn)

if __name__ == "__main__":
    populate_dummy_data()
    print("Starting Vanna Flask app with LLM Studio integration")
    app.run()
