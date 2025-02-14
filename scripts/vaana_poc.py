from vanna.base import VannaBase
import sqlite3
import requests
import json
import numpy as np
from typing import List, Dict, Any, Optional

class LLMStudioVanna(VannaBase):
    def __init__(self, base_url="http://127.0.0.1:1234"):
        self.base_url = base_url
        super().__init__()

    def _call_llm_studio(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/v1/completions",
                json={
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )
            result = response.json()
            return result.get('choices', [{}])[0].get('text', '').strip()
        except Exception as e:
            print(f"Error calling LLM Studio: {e}")
            return ""

    def generate_sql(self, question: str) -> str:
        prompt = f"Generate SQL query for: {question}\n\nSQL:"
        return self._call_llm_studio(prompt)

    def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * 384  # Return a 384-dimensional zero vector

    def add_ddl(self, ddl: str) -> bool:
        return True

    def add_documentation(self, documentation: str) -> bool:
        return True

    def add_question_sql(self, question: str, sql: str) -> bool:
        return True

    def get_related_ddl(self, question: str) -> List[str]:
        return []

    def get_related_documentation(self, question: str) -> List[str]:
        return []

    def get_similar_question_sql(self, question: str) -> List[Dict[str, str]]:
        return []

    def get_training_data(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "ddl": [],
            "documentation": [],
            "question_sql": []
        }

    def remove_training_data(self) -> bool:
        return True

    def system_message(self) -> str:
        return "You are a helpful AI assistant that generates SQL queries."

    def user_message(self, question: str) -> str:
        return f"Please generate a SQL query for: {question}"

    def assistant_message(self, sql: str) -> str:
        return f"Here's the SQL query: {sql}"

    def submit_prompt(self, prompt: str) -> str:
        return self._call_llm_studio(prompt)

def main():
    vanna_model = LLMStudioVanna()

    conn = sqlite3.connect('carbon_footprint.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS batteries (
        id INTEGER PRIMARY KEY,
        type TEXT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
    ''')

    sample_data = [
        ('Lithium-Ion', 75.0, 7500.0),
        ('NMC', 85.0, 8000.0),
        ('LFP', 60.0, 5500.0)
    ]
    cursor.executemany(
        'INSERT OR IGNORE INTO batteries (type, capacity_kwh, carbon_footprint_kg) VALUES (?, ?, ?)',
        sample_data
    )
    conn.commit()

    ddl = '''
    CREATE TABLE batteries (
        id INTEGER PRIMARY KEY,
        type TEXT,
        capacity_kwh FLOAT,
        carbon_footprint_kg FLOAT
    )
    '''
    vanna_model.add_ddl(ddl)

    doc = '''
    The batteries table contains information about different battery types and their carbon footprint.
    - type: The type of battery technology
    - capacity_kwh: The capacity of the battery in kilowatt-hours
    - carbon_footprint_kg: The carbon footprint in kilograms of CO2 equivalent
    '''
    vanna_model.add_documentation(doc)


    questions = [
        "What is the carbon footprint of all battery types?",
        "Which battery type has the highest carbon footprint?",
        "What is the average carbon footprint per kWh for each battery type?"
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        try:
            sql_query = vanna_model.generate_sql(question)
            print(f"Generated SQL: {sql_query}")
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            print(f"Results: {results}")
        except Exception as e:
            print(f"Error: {e}")

    conn.close()

if __name__ == "__main__":
    main()