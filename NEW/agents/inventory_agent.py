import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from ..config.llm import get_llm
from ..tools.inventory_tools import ReadInventoryTool, UpdateInventoryTool, ForecastInventoryTool

# Initialize the LLM and memory
llm = get_llm()
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Initialize the tools
inventory_tools = [
    ReadInventoryTool(),
    UpdateInventoryTool(),
    ForecastInventoryTool()
]

# Define the agent's prompt
inventory_prompt_template = """
You are a specialized inventory management agent for an ERP system. Your goal is to manage stock levels, provide inventory forecasts, and answer questions about products. You have access to the following tools:
{tools}

Use these tools to answer the user's questions. You should always try to use the most specific tool for the task.

Begin!

Question: {input}
{agent_scratchpad}
"""

# Create the agent executor
inventory_executor = AgentExecutor(
    agent=create_react_agent(llm, inventory_tools, PromptTemplate.from_template(inventory_prompt_template)),
    tools=inventory_tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)
