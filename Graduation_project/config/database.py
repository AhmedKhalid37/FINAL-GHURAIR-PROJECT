import sqlite3
import os
from pathlib import Path

# Database configuration
DB_PATH = Path(__file__).parent.parent / "erp_sample.db"

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def get_table_names():
    """Get all table names from the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        print(f"Error getting table names: {e}")
        return []

def execute_query(query, params=None):
    """Execute a query and return results"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
        else:
            conn.commit()
            results = cursor.lastrowid
        
        conn.close()
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def log_tool_call(user_id, agent_name, tool_name, input_data, output_data, execution_time_ms, status="success", error_message=None):
    """Log a tool call to the database"""
    query = """
    INSERT INTO tool_calls (user_id, agent_name, tool_name, input_data, output_data, execution_time_ms, status, error_message)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (user_id, agent_name, tool_name, str(input_data), str(output_data), execution_time_ms, status, error_message)
    return execute_query(query, params)

def log_conversation(user_id, session_id, message_type, content, agent_name=None, metadata=None):
    """Log a conversation message to the database"""
    query = """
    INSERT INTO conversations (user_id, session_id, message_type, content, agent_name, metadata)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (user_id, session_id, message_type, content, agent_name, str(metadata) if metadata else None)
    return execute_query(query, params)
