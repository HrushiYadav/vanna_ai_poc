import os
import sqlite3
import requests
import json
import numpy as np
import re
import streamlit as st
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import openai
import pandas as pd

os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

COLUMN_ALIASES = {
    "id": "ID",
    "part_number": "Part Number",
    "type": "Battery Type",
    "capacity_kwh": "Capacity (kWh)",
    "carbon_footprint_kg": "Carbon Footprint (kg CO2e)"
}

class MyVanna:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint="https://your-endpoint/azure.com/",
            api_key="key",
            api_version="ver"
        )
        self.deployment_name = "modelName"  

    def submit_prompt(self, prompt: str) -> str:
        try:
            table_schema = (
                "The database has the following table:\n"
                "Table: batteries\n"
                "- id (INTEGER PRIMARY KEY)\n"
                "- part_number (TEXT) -- Unique identifier for the battery part\n"
                "- type (TEXT) -- The type of battery technology. Must be referenced correctly in queries.\n"
                "- capacity_kwh (FLOAT) -- The capacity in kWh\n"
                "- carbon_footprint_kg (FLOAT) -- The carbon footprint in kg CO2e\n"
                "Ensure all queries correctly use `type` as a categorical value (e.g., 'Type-1') instead of numbers."
            )

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an AI that provides structured responses for battery carbon footprint analysis. "
                                                      "Always generate SQL queries using the table `batteries` and its correct column names. "
                                                      "Ensure that the columns exist before generating a query. "
                                                      "Return only the SQL query without any markdown formatting (no ```sql ... ```)."},
                    {"role": "user", "content": table_schema + "\n\n" + prompt}
                ],
                max_tokens=500,
                temperature=0.3  
            )
            return response.choices[0].message.content.strip()
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return ""
        except openai.OpenAIError as e:
            print(f"❌ OpenAI API Error: {e}")
            return ""

vn = MyVanna()

def mask_part_numbers(query: str) -> str:
    masked_query = re.sub(r'\b(PART-\d+)\b', '[MASKED]', query)
    print(f"Before Masking: {query}")
    print(f"After Masking: {masked_query}")
    return masked_query

def query_database(sql_query):
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    conn = sqlite3.connect('carbon_footprint.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        column_names = [desc[0] for desc in cursor.description]  
        results = cursor.fetchall()
        conn.close()
        return results, column_names if results else ([], [])
    except sqlite3.Error as e:
        conn.close()
        print(f"SQLite Error: {e}")
        return [], []

def populate_dummy_data():
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
        (f'PART-{i}', f'Type-{i%5}', round(np.random.uniform(50, 150), 2), round(np.random.uniform(5000, 15000), 2))
        for i in range(1, 50)
    ]
    
    cursor.executemany(
        'INSERT INTO batteries (part_number, type, capacity_kwh, carbon_footprint_kg) VALUES (?, ?, ?, ?)',
        dummy_data
    )
    conn.commit()
    conn.close()

def chat_ui():
    st.set_page_config(page_title="Battery Carbon Footprint", layout="wide")
    st.title("🔋 Battery Carbon Footprint Analysis")
    st.write("Ask questions about the battery carbon footprint database.")
    
    user_input = st.text_input("🔎 Enter your question:")
    if st.button("Ask 📩"): 
        if user_input.strip():
            masked_query = mask_part_numbers(user_input)
            sql_query = vn.submit_prompt(f"Generate SQL query for \n Don't add ID column in query: {masked_query}\n\nSQL:")
            
            if sql_query:
                st.markdown("**📝 Generated SQL Query:**")
                st.code(sql_query, language='sql')

                results, column_names = query_database(sql_query)
                
                if results:
                    alias_columns = [COLUMN_ALIASES.get(col, col) for col in column_names if col != "id"]
                    df = pd.DataFrame(results, columns=alias_columns)
                    st.markdown("**📊 Results:**")
                    st.table(df)

                    summary_prompt = f"Generate a structured AI summary for easy readability, including all relevant column names: {df.to_dict()}"
                    summary_response = vn.submit_prompt(summary_prompt)
                    st.markdown(f"💡 AI Summary: {summary_response}")
                else:
                    st.warning("⚠️ No valid data found. Please refine your query.")
            else:
                st.error("❌ No valid SQL query generated.")

if __name__ == "__main__":
    populate_dummy_data()
    chat_ui()
