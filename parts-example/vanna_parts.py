from vanna.base import VannaBase
import sqlite3
import requests
import json
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
                    "max_tokens": 500,
                    # "stop:":[";"]  test for getting proper response
                }
            )
            result = response.json()
            return result.get('choices', [{}])[0].get('text', '').strip()
        except Exception as e:
            print(f"Error calling LLM Studio: {e}")
            return ""

    def generate_sql(self, question: str) -> str:
        schema_context = """
        Available tables and their columns:
        - manufacturers: manufacturer_id, name, country, contact_email, quality_rating
        - distributors: distributor_id, name, region, contact_email, delivery_rating
        - parts: part_id, name, manufacturer_id, description, diameter_mm, weight_kg, material, carbon_footprint_kg, price
        - part_distributors: part_id, distributor_id, stock_quantity, lead_time_days
        """
        
        prompt = f"""
        {schema_context}
        
        Generate a SQL query for the following question: {question}
        
        The query should be valid SQLite SQL. Return only the SQL query, nothing else.
        
        SQL:"""
        
        return self._call_llm_studio(prompt)

    def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * 384

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

    conn = sqlite3.connect('parts.db')
    cursor = conn.cursor()

    questions = [
        "What parts does TechCore Industries manufacture?",
        "List all distributors that handle parts with carbon footprint less than 10kg",
        "What is the average price of parts for each manufacturer?",
        "Which parts have the highest stock quantity across all distributors?",
        "List all parts and their manufacturers where the manufacturer quality rating is above 4.7"
    ]

    for question in questions:
        print(f"\n\nQuestion: {question}")
        try:
            sql_query = vanna_model.generate_sql(question)
            print(f"\nGenerated SQL: {sql_query}")
            
            if sql_query:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                
                column_names = [description[0] for description in cursor.description]
                
                print("\nResults:")
                print("Columns:", ", ".join(column_names))
                for row in results:
                    print(row)
        except Exception as e:
            print(f"Error executing query: {e}")

    conn.close()

if __name__ == "__main__":
    main()