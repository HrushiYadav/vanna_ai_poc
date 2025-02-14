from vanna.local import LocalContext_ChromaDB
from vanna.base import VannaBase
import sqlite3

# Initialize Vanna with Chroma DB
vanna_model = VannaBase(model='my_model', config=LocalContext_ChromaDB())

# Load your local LLM (LLM Studio)
def generate_sql_with_llm_studio(question: str) -> str:
    # Replace this with your LLM Studio API or logic
    # Example: Use LLM Studio's API to generate SQL
    response = llm_studio.generate(question)  # Replace with actual LLM Studio call
    return response['sql']

# Ask a question
question = "What is the carbon footprint of the Battery?"
sql_query = generate_sql_with_llm_studio(question)

print("Generated SQL Query:", sql_query)

# Execute the query on your database
conn = sqlite3.connect('../data/parts.db')
cursor = conn.cursor()
cursor.execute(sql_query)
result = cursor.fetchall()

print("Query Result:", result)