# agents/router_agent.py
import os
import sys
from pathlib import Path
import sqlite3
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import tool
from langchain.memory import ConversationBufferWindowMemory
from config.database import get_table_names
from config.llm import get_llm
from config.prompts import import_get_react_prompt

# -----------------------
# Safe imports for specialized agents
# -----------------------
try:
    from agents.sales_agent import executor as sales_executor
except Exception:
    class _EchoExecutor:
        def invoke(self, inputs):
            return {"output": f"[Sales Stub] I would process: {inputs.get('input')}"}
    sales_executor = _EchoExecutor()

try:
    from agents.finance_agent import executor as finance_executor
except Exception:
    class _EchoExecutor:
        def invoke(self, inputs):
            return {"output": f"[Finance Stub] I would process: {inputs.get('input')}"}
    finance_executor = _EchoExecutor()

try:
    from agents.inventory_agent import executor as inventory_executor
except Exception:
    class _EchoExecutor:
        def invoke(self, inputs):
            return {"output": f"[Inventory Stub] I would process: {inputs.get('input')}"}
    inventory_executor = _EchoExecutor()

try:
    from agents.analytics_agent import executor as analytics_executor
except Exception:
    class _EchoExecutor:
        def invoke(self, inputs):
            return {"output": f"[Analytics Stub] I would process: {inputs.get('input')}"}
    analytics_executor = _EchoExecutor()

# -----------------------
# Memory + LLM
# -----------------------
llm = get_llm()
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# -----------------------
# Database helpers
# -----------------------
DB_PATH = Path(__file__).parent / "erp_sample.db"
SESSION_ID = os.getenv("ERP_SESSION_ID", "demo-session")
USER_ID = os.getenv("ERP_USER_ID", "demo-user")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Ensure tables exist
with get_db_connection() as _conn:
    cur = _conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            user_input TEXT,
            agent_output TEXT,
            agent TEXT,
            success INTEGER
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            agent TEXT,
            inputs TEXT,
            outputs TEXT,
            success INTEGER
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            request TEXT,
            agent TEXT,
            status TEXT,
            reasons TEXT
        );
    """)
    _conn.commit()

# -----------------------
# Governance + Logging
# -----------------------
def check_governance(user_request: str, domain: str) -> dict:
    risky_phrases = [
        "export all", "delete all", "drop table", "truncate", "wipe",
        "download financials", "mass update", "bulk delete", "transfer funds"
    ]
    domain_sensitive = {
        "finance": ["payments", "payout", "transfer", "invoice export"],
        "inventory": ["adjust all stock", "zero stock"],
        "sales": ["export customers", "delete leads"],
        "analytics": ["export report", "download report"]
    }
    reasons = [p for p in risky_phrases if p in user_request.lower()]
    for phrase in domain_sensitive.get(domain, []):
        if phrase in user_request.lower():
            reasons.append(f"domain-sensitive: {phrase}")
    if reasons:
        return {"needs_approval": True, "risk_level": "HIGH", "reasons": reasons}
    return {"needs_approval": False, "risk_level": "LOW", "reasons": []}

def log_tool_call(agent: str, inputs: dict, outputs: str, success: bool):
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO tool_calls (session_id, user_id, agent, inputs, outputs, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (SESSION_ID, USER_ID, agent, json.dumps(inputs), outputs, int(success)),
            )
            conn.commit()
    except Exception as e:
        print(f"Tool call logging error: {e}")

def log_conversation(user_input: str, agent_output: str, agent: str, success: bool):
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (session_id, user_id, user_input, agent_output, agent, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (SESSION_ID, USER_ID, user_input, agent_output, agent, int(success)),
            )
            conn.commit()
    except Exception as e:
        print(f"Conversation logging error: {e}")

def llm_classify_domain(user_request: str) -> str:
    prompt = f"""
    Classify the following ERP user request into one domain:
    - sales
    - finance
    - inventory
    - analytics

    Request: "{user_request}"
    Answer with only one domain.
    """
    try:
        result = llm.invoke(prompt)
        domain = result.content.strip().lower()
        if domain not in ["sales", "finance", "inventory", "analytics"]:
            return "unknown"
        return domain
    except Exception as e:
        print(f"LLM classification error: {e}")
        return "unknown"

# -----------------------
# Specialized Tools
# -----------------------
@tool
def execute_with_sales_agent(user_request: str) -> str:
    try:
        result = sales_executor.invoke({"input": user_request})
        return result['output']
    except Exception as e:
        return f"Sales Agent Error: {str(e)}"

@tool
def execute_with_finance_agent(user_request: str) -> str:
    try:
        result = finance_executor.invoke({"input": user_request})
        return result['output']
    except Exception as e:
        return f"Finance Agent Error: {str(e)}"

@tool
def execute_with_inventory_agent(user_request: str) -> str:
    try:
        result = inventory_executor.invoke({"input": user_request})
        return result['output']
    except Exception as e:
        return f"Inventory Agent Error: {str(e)}"

@tool
def execute_with_analytics_agent(user_request: str) -> str:
    try:
        result = analytics_executor.invoke({"input": user_request})
        return result['output']
    except Exception as e:
        return f"Analytics Agent Error: {str(e)}"

# -----------------------
# Classify + Route
# -----------------------
@tool
def classify_and_route(user_request: str) -> str:
    domain = llm_classify_domain(user_request)
    if domain == "unknown":
        request_lower = user_request.lower()
        scores = {
            'sales': sum(1 for kw in ['customer','lead','order','sale','client'] if kw in request_lower),
            'finance': sum(1 for kw in ['invoice','payment','accounting','budget','financial'] if kw in request_lower),
            'inventory': sum(1 for kw in ['stock','product','warehouse','item'] if kw in request_lower),
            'analytics': sum(1 for kw in ['report','dashboard','metric','chart','insight'] if kw in request_lower)
        }
        domain, _ = max(scores.items(), key=lambda x: x[1])

    gov = check_governance(user_request, domain)
    if gov["needs_approval"]:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO approvals (session_id, user_id, request, agent, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (SESSION_ID, USER_ID, user_request, domain, "PENDING", ", ".join(gov["reasons"]))
            )
            conn.commit()
        return f"⚠️ Request flagged as {gov['risk_level']} risk. Reasons: {', '.join(gov['reasons'])}"

    # Route to agent
    try:
        if domain == "sales":
            output = execute_with_sales_agent(user_request)
        elif domain == "finance":
            output = execute_with_finance_agent(user_request)
        elif domain == "inventory":
            output = execute_with_inventory_agent(user_request)
        elif domain == "analytics":
            output = execute_with_analytics_agent(user_request)
        else:
            output = "❓ Unable to classify request."

        memory.chat_memory.add_user_message(user_request)
        memory.chat_memory.add_ai_message(output)
        log_tool_call(domain, {"user_request": user_request}, output, success=True)
        log_conversation(user_request, output, domain, success=True)
        return output
    except Exception as e:
        log_tool_call(domain, {"user_request": user_request}, str(e), success=False)
        log_conversation(user_request, str(e), domain, success=False)
        return f"Error routing request: {str(e)}"

# -----------------------
# System Info
# -----------------------
@tool
def get_system_info() -> str:
    try:
        tables = get_table_names()
        key_tables = ['customers','orders','products','invoices','leads','stock']
        counts = {}
        with get_db_connection() as conn:
            cur = conn.cursor()
            for tbl in key_tables:
                try:
                    cur.execute(f"SELECT COUNT(1) FROM {tbl}")
                    counts[tbl] = cur.fetchone()[0]
                except Exception:
                    counts[tbl] = 0
