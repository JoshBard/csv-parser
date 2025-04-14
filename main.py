from openai import OpenAI
import sqlite3
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_PATH = "my_database.db"
MODEL = "gpt-3.5-turbo"

def connect_db():
    return sqlite3.connect(DB_PATH)

def get_table_schemas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = ""
    for (table,) in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        schema += f"Table: {table}\n"
        for col in cols:
            schema += f"  {col[1]} ({col[2]})\n"
    return schema.strip()

def ask_llm_for_sql(schema, user_request):
    prompt = f"""
You are a helpful SQLite assistant. The following is the table schema:

{schema}

The user wants to do this: "{user_request}"

Write a SQL query for SQLite that accomplishes this task.
Only return the SQL query with no extra comments.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def execute_query(conn, sql):
    try:
        df = pd.read_sql_query(sql, conn)
        print("\nQuery Results:\n")
        print(df)
    except Exception as e:
        print(f"Error executing query: {e}")

def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    if not tables:
        print("No tables found.")
    else:
        print("Tables:")
        for table in tables:
            print(f"  - {table[0]}")

def load_csv_to_table(conn):
    csv_path = input("Enter CSV file path: ").strip()
    if not os.path.isfile(csv_path):
        print("File not found.")
        return
    table_name = input("Enter table name to load into: ").strip()
    try:
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"CSV loaded into table '{table_name}' successfully.")
    except Exception as e:
        print(f"Failed to load CSV: {e}")

def main():
    print(" SQL Assistant ")
    conn = connect_db()

    while True:
        print("\nChoose an option:")
        print("1. Load CSV into a table")
        print("2. Ask a question (natural language)")
        print("3. List tables")
        print("4. Exit")
        choice = input("Enter choice (1-4): ").strip()

        if choice == '1':
            load_csv_to_table(conn)
        elif choice == '2':
            user_input = input("Ask your question: ").strip()
            schema = get_table_schemas(conn)
            sql = ask_llm_for_sql(schema, user_input)
            print(f"\nGenerated SQL:\n{sql}")
            execute_query(conn, sql)
        elif choice == '3':
            list_tables(conn)
        elif choice == '4':
            print("Goodbye.")
            break
        else:
            print("Invalid option.")

    conn.close()

if __name__ == "__main__":
    main()
