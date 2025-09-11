import sqlite3
from pathlib import Path
from typing import Optional, Dict

# Correct pathing to the database file
DB_NAME = "erp.db"
DB_PATH = Path(__file__).resolve().parents[1] / "database" / DB_NAME

def get_connection():
    """Establishes and returns a new database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    return conn

def get_db_schema():
    """
    Get database schema information for all tables.
    Returns a dictionary where keys are table names and values are lists of column names.
    """
    schema = {}
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            schema[table] = columns
    except sqlite3.Error as e:
        print(f"Failed to retrieve database schema: {e}")
        return {}
    finally:
        conn.close()
        
    return schema

def get_db_name():
    """Get database name for queries."""
    return str(DB_PATH.name)

# This is a critical function to be used by the analytics agent's tools
def get_db_info() -> Dict[str, str]:
    """Returns the database name and schema as a dictionary."""
    return {
        "db_name": get_db_name(),
        "db_schema": str(get_db_schema())
    }

def initialize_db():
    """Initializes the database connection."""
    conn = get_connection()
    conn.close()
    
if __name__ == '__main__':
    initialize_db()
    print(f"Database initialized at: {DB_PATH}")
    print("\nDatabase Schema:")
    schema = get_db_schema()
    for table, columns in schema.items():
        print(f"Table: {table}")
        print(f"Columns: {', '.join(columns)}")
