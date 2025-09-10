# Smart Router Agent - Automatically routes and executes requests with specialized agents

import os
import sys
from pathlib import Path
import sqlite3
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import tool
from langchain.memory import ConversationBufferWindowMemory
from config.database import get_table_names
from config.llm import get_llm
from config.prompts import import_get_react_prompt

# -----------------------
# Safe imports for specialized agents (fallback to stubs if missing)
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
# Orchestrator DB helpers (uses erp_sample.db)
# -----------------------
DB_PATH = Path(__file__).parent / "erp_sample.db"
SESSION_ID = os.getenv("ERP_SESSION_ID", "demo-session")
USER_ID = os.getenv("ERP_USER_ID", "demo-user")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Ensure tables exist (idempotent) for orchestrator logs/approvals
# These will be no-ops if the tables already exist
with get_db_connection() as _conn:
    cur = _conn.cursor()
    cur.execute(
        """
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
        """
    )
    cur.execute(
        """
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
        """
    )
    cur.execute(
        """
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
        """
    )
    _conn.commit()


# -----------------------
# Governance + Logging helpers
# -----------------------

def check_governance(user_request: str, domain: str) -> dict:
    """Simple policy check that flags risky operations requiring approval.
    Returns dict: {needs_approval: bool, risk_level: str, reasons: [str]}
    """
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
    """Persist tool call metadata for observability."""
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
    """Persist conversation turns for memory/audit."""
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
    """Use LLM to classify which agent should handle the request."""
    classification_prompt = f"""
    Classify the following ERP user request into one domain:
    - sales
    - finance
    - inventory
    - analytics

    Request: "{user_request}"
    Answer with only one domain.
    """
    try:
        result = llm.invoke(classification_prompt)
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
    """Execute a request using the Sales Agent for customer, order, and lead management.
    Input: user's request/question about sales, customers, orders, or leads"""
    try:
        print(f"Routing to Sales Agent: {user_request}")
        result = sales_executor.invoke({"input": user_request})
        return f"Sales Agent Response: {result['output']}"
    except Exception as e:
        return f"Sales Agent Error: {str(e)}"

@tool
def execute_with_finance_agent(user_request: str) -> str:
    """Execute a request using the Finance Agent for financial data and accounting.
    Input: user's request/question about finances, invoices, payments, or accounting"""
    try:
        print(f"Routing to Finance Agent: {user_request}")
        result = finance_executor.invoke({"input": user_request})
        return f"Finance Agent Response: {result['output']}"
    except Exception as e:
        return f"Finance Agent Error: {str(e)}"

@tool
def execute_with_inventory_agent(user_request: str) -> str:
    """Execute a request using the Inventory Agent for stock and product management.
    Input: user's request/question about inventory, stock levels, or products"""
    try:
        print(f"Routing to Inventory Agent: {user_request}")
        result = inventory_executor.invoke({"input": user_request})
        return f"Inventory Agent Response: {result['output']}"
    except Exception as e:
        return f"Inventory Agent Error: {str(e)}"

@tool
def execute_with_analytics_agent(user_request: str) -> str:
    """Execute a request using the Analytics Agent for reports and business intelligence.
    Input: user's request/question about analytics, reports, or business insights"""
    try:
        print(f"Routing to Analytics Agent: {user_request}")
        result = analytics_executor.invoke({"input": user_request})
        return f"Analytics Agent Response: {result['output']}"
    except Exception as e:
        return f"Analytics Agent Error: {str(e)}"


# -----------------------
# Classify + Route
# -----------------------

@tool
def classify_and_route(user_request: str) -> str:
    """Automatically classify the user request and route it to the appropriate specialist agent.
    Includes governance (approval flows), logging, and memory persistence."""

    # --- Step 1: Try LLM classification ---
    best_domain = llm_classify_domain(user_request)

    # --- Step 2: Fallback to keyword scoring ---
    if best_domain == "unknown":
        request_lower = user_request.lower()
        scores = {
            'sales': sum(1 for kw in ['customer','lead','prospect','sale','order','crm','contact','deal','client'] if kw in request_lower),
            'finance': sum(1 for kw in ['invoice','payment','accounting','revenue','expense','budget','financial','money','cost'] if kw in request_lower),
            'inventory': sum(1 for kw in ['stock','inventory','product','warehouse','supply','procurement','vendor','item'] if kw in request_lower),
            'analytics': sum(1 for kw in ['report','analytics','dashboard','metrics','analysis','trend','chart','insight'] if kw in request_lower)
        }
        best_domain, _ = max(scores.items(), key=lambda x: x[1])

    print(f"Auto-routing to {best_domain} agent (via LLM+keywords)")

    # --- Step 3: Governance Check ---
    gov_result = check_governance(user_request, best_domain)
    if gov_result["needs_approval"]:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO approvals (session_id, user_id, request, agent, status, reasons)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (SESSION_ID, USER_ID, user_request, best_domain, "PENDING", ", ".join(gov_result["reasons"]))
            )
            conn.commit()
        return f"⚠️ This request is flagged as {gov_result['risk_level']} risk and requires approval.\nReasons: {', '.join(gov_result['reasons'])}"

    # --- Step 4: Route to the correct agent ---
    try:
        if best_domain == 'sales':
            result = execute_with_sales_agent(user_request)
        elif best_domain == 'finance':
            result = execute_with_finance_agent(user_request)
        elif best_domain == 'inventory':
            result = execute_with_inventory_agent(user_request)
        elif best_domain == 'analytics':
            result = execute_with_analytics_agent(user_request)
        else:
            result = "❓ Unable to classify request."

        # --- Step 5: Update Memory ---
        memory.chat_memory.add_user_message(user_request)
        memory.chat_memory.add_ai_message(result)

        # --- Step 6: Log Tool Calls & Conversation ---
        log_tool_call(best_domain, {"user_request": user_request}, result, success=True)
        log_conversation(user_request, result, best_domain, success=True)

        return result

    except Exception as e:
        error_msg = f"Error routing to {best_domain} agent: {str(e)}"
        log_tool_call(best_domain, {"user_request": user_request}, error_msg, success=False)
        log_conversation(user_request, error_msg, best_domain, success=False)
        return error_msg


# -----------------------
# System Info
# -----------------------

@tool
def get_system_info() -> str:
    """Get information about the ERP system and available agents.
    No input required."""
    try:
        tables = get_table_names()
        key_tables = ['customers', 'orders', 'products', 'invoices', 'leads', 'stock']
        counts = {}
        with get_db_connection() as conn:
            cur = conn.cursor()
            for tbl in key_tables:
                try:
                    cur.execute(f"SELECT COUNT(1) FROM {tbl}")
                    counts[tbl] = cur.fetchone()[0]
                except Exception:
                    counts[tbl] = 0
        info = {
            "system": "Smart Agentic ERP System",
            "available_agents": [
                "Sales Agent - Customer management, orders, leads (auto-routed)",
                "Finance Agent - Invoices, payments, accounting (auto-routed)",
                "Inventory Agent - Stock management, products (auto-routed)",
                "Analytics Agent - Reports and business intelligence (auto-routed)"
            ],
            "database_tables": tables,
            "row_counts": counts,
            "key_tables": [t for t in tables if t in key_tables]
        }
        lines = [
            f"Smart ERP System information:",
            f"- System: {info['system']}",
            f"- Database Tables: {info['database_tables']}",
            f"- Key Tables: {', '.join(info['key_tables'])}",
            "Row counts:",
        ]
        for t in key_tables:
            lines.append(f"  - {t}: {counts.get(t, 0)}")
        lines.append("Available Specialized Agents (Auto-Routing):")
        for agent in info["available_agents"]:
            lines.append(f"  - {agent}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving system info: {str(e)}"


# -----------------------
# Agent Setup
# -----------------------

tools = [
    execute_with_sales_agent,
    execute_with_finance_agent,
    execute_with_inventory_agent,
    execute_with_analytics_agent,
    classify_and_route,
    get_system_info
]

prompt = import_get_react_prompt()

router_agent = create_react_agent(
    llm,
    tools,
    prompt
)

router_executor = AgentExecutor(
    agent=router_agent,
    tools=tools,
    memory=memory,
    verbose=True
)


if __name__ == "__main__":
    print("Smart Router Agent ready. Type 'system' for info or 'quit' to exit.")
    while True:
        try:
            user_inp = input("You: ").strip()
            if not user_inp:
                continue
            if user_inp.lower() in ["quit", "exit"]:
                print("Exiting.")
                break
            if user_inp.lower() == "system":
                print(get_system_info())
                continue
            # Use classify_and_route tool directly for demo simplicity
            print(classify_and_route(user_inp))
        except KeyboardInterrupt:
            print("\nInterrupted. Bye.")
            break
        except Exception as e:
            print(f"Error: {e}")
