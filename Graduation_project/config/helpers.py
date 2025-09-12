# config/helpers.py
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "erp.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def check_governance(user_request: str, domain: str) -> dict:
    """Check if a request is risky and needs approval."""
    risky_phrases = ["export all", "delete all", "download financials", "wipe", "truncate"]
    reasons = [phrase for phrase in risky_phrases if phrase in user_request.lower()]
    if reasons:
        return {"needs_approval": True, "risk_level": "HIGH", "reasons": reasons}
    return {"needs_approval": False, "risk_level": "LOW", "reasons": []}

def log_tool_call(agent: str, input_data: dict, output: str, success: bool):
    """Log tool calls to database."""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO tool_calls (agent, input_data, output, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (agent, str(input_data), output, int(success), datetime.utcnow()))
        conn.commit()

def log_conversation(user_input: str, response: str, agent: str, success: bool):
    """Log conversation exchanges."""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO conversations (user_input, response, agent, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_input, response, agent, int(success), datetime.utcnow()))
        conn.commit()

def remember(key: str, value: str):
    """Save a memory item."""
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO memory (key, value, timestamp) VALUES (?, ?, ?)
        """, (key, value, datetime.utcnow()))
        conn.commit()

def recall(key: str) -> str:
    """Retrieve memory item."""
    with get_db_connection() as conn:
        cur = conn.execute("SELECT value FROM memory WHERE key = ? ORDER BY timestamp DESC LIMIT 1", (key,))
        row = cur.fetchone()
        return row[0] if row else None
