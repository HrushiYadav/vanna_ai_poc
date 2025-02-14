from vanna.base import VannaBase
from vanna.default import VannaDefault
import sqlite3

# Initialize Vanna with the default configuration
vanna_model = VannaDefault(model='my_model')

# Ask a question
question = "What is the carbon footprint of the Battery?"
sql_query = vanna_model.generate_sql(question=question)

print("Generated SQL Query:", sql_query)

# Execute the query on your database
conn = sqlite3.connect('../data/parts.db')
cursor = conn.cursor()
cursor.execute(sql_query)
result = cursor.fetchall()

print("Query Result:", result)