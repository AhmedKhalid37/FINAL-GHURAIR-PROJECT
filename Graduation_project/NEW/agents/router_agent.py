import json
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import Tool

# Use absolute imports to avoid relative import issues when running without package context
from config.llm import get_llm
from config.prompts import import_get_react_prompt
from tools.base_tool import register_tool, BaseTool
from tools.analytics_tools import TextToSQLTool
from tools.inventory_tools import InventorySQLReadTool as InventoryReadTool, InventorySQLWriteTool as InventoryWriteTool, ForecastTool as InventoryForecastTool
from tools.anomaly_detector_tool import AnomalyDetectorTool
from tools.sales_rag_tool import SalesRAGTool

from agents.analytics_agent import analytics_executor
from agents.inventory_agent import inventory_executor
# Note: finance_agent and sales_agent expose class-based handlers, not executors

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
    def _run(self, query: str):
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

def provide_system_info(_: str = ""):
    return get_system_info()

# Define tools for the router agent
tools = [
    Tool(
        name="classify_and_route",
        func=lambda query: ClassifyAndRouteTool()._run(query),
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
        name="get_system_info",
        func=provide_system_info,
        description="Lists available specialized agents in the system."
    )
]

# Set up the memory for the router agent
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Prepare prompt with tool metadata to satisfy required variables
tool_strings = "\n".join([f"{t.name}: {t.description}" for t in tools])
tool_names = ", ".join([t.name for t in tools])
router_prompt = import_get_react_prompt().partial(tools=tool_strings, tool_names=tool_names)

# Create the router agent
router_executor = AgentExecutor(
    agent=create_react_agent(llm, tools, router_prompt),
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)
