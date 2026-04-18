import mysql.connector

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Ajaya1@2&3",
    "charset":  "utf8mb4",
}

def execute_sql_file():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    with open("01_star_schema_mysql.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    
    # Split by statements
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for statement in statements:
        try:
            if statement:
                cur.execute(statement)
        except Exception as e:
            print(f"Error executing statement: {statement[:50]}... \n{e}")
    conn.commit()
    conn.close()
    print("Schema updated successfully")

if __name__ == "__main__":
    execute_sql_file()
