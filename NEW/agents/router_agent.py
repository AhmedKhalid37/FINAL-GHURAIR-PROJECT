import json
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import Tool

# Corrected imports using absolute paths from the project root
from ..config.llm import get_llm
from ..config.prompts import import_get_react_prompt
from ..tools.base_tool import register_tool, BaseTool
from ..tools.analytics_tools import TextToSQLTool
from ..tools.inventory_tools import InventoryReadTool, InventoryWriteTool, InventoryForecastTool
from ..tools.anomaly_detector_tool import AnomalyDetectorTool
from ..tools.sales_rag_tool import SalesRAGTool

# Relative imports for other agents in the same folder are correct
from .analytics_agent import analytics_executor
from .inventory_agent import inventory_executor
from .finance_agent import finance_executor
from .sales_agent import sales_executor

llm = get_llm()

# Define the router tool functions
@register_tool
class ClassifyAndRouteTool(BaseTool):
    name = "classify_and_route"
    description = """
    Routes a query to the appropriate specialized agent based on the query's topic.
    This tool should be used first to determine which agent should handle the user's request.
    The input to this tool is the original user query.
    """
    def run(self, query: str):
        # A simple keyword-based router, which can be improved with an LLM call
        query_lower = query.lower()
        if "analytics" in query_lower or "report" in query_lower or "data" in query_lower or "business intelligence" in query_lower or "sql" in query_lower:
            return "analytics_agent"
        elif "inventory" in query_lower or "stock" in query_lower or "product" in query_lower or "level" in query_lower or "unit" in query_lower or "forecast" in query_lower:
            return "inventory_agent"
        elif "sales" in query_lower or "customer" in query_lower or "feedback" in query_lower or "sentiment" in query_lower:
            return "sales_agent"
        elif "finance" in query_lower or "payment" in query_lower or "invoice" in query_lower or "transaction" in query_lower or "anomaly" in query_lower or "fraud" in query_lower:
            return "finance_agent"
        else:
            return "general"

def get_system_info():
    """Provides a list of available specialized agents."""
    return "Available agents: analytics_agent, inventory_agent, finance_agent, sales_agent."

def execute_with_analytics_agent(query: str):
    """Executes a query with the analytics agent."""
    return analytics_executor.invoke({"input": query})['output']

def execute_with_inventory_agent(query: str):
    """Executes a query with the inventory agent."""
    return inventory_executor.invoke({"input": query})['output']

def execute_with_finance_agent(query: str):
    """Executes a query with the finance agent."""
    return finance_executor.invoke({"input": query})['output']

def execute_with_sales_agent(query: str):
    """Executes a query with the sales agent."""
    return sales_executor.invoke({"input": query})['output']

# Define tools for the router agent
tools = [
    Tool(
        name="classify_and_route",
        func=lambda query: ClassifyAndRouteTool().run(query),
        description="Routes a query to the appropriate specialized agent."
    ),
    Tool(
        name="execute_with_analytics_agent",
        func=execute_with_analytics_agent,
        description="Executes a query with the analytics agent. Use for queries about business data, reports, or SQL."
    ),
    Tool(
        name="execute_with_inventory_agent",
        func=execute_with_inventory_agent,
        description="Executes a query with the inventory agent. Use for queries about product stock levels, inventory updates, or forecasts."
    ),
    Tool(
        name="execute_with_finance_agent",
        func=execute_with_finance_agent,
        description="Executes a query with the finance agent. Use for queries about invoices, payments, or financial anomalies."
    ),
    Tool(
        name="execute_with_sales_agent",
        func=execute_with_sales_agent,
        description="Executes a query with the sales agent. Use for queries about customers or sales-related information."
    )
]

# Set up the memory for the router agent
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Create the router agent
router_executor = AgentExecutor(
    agent=create_react_agent(llm, tools, import_get_react_prompt()),
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)
