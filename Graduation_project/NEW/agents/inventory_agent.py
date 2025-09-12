import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from config.llm import get_llm
from config.database import DB_PATH
from tools.inventory_tools import InventorySQLReadTool as ReadInventoryTool, InventorySQLWriteTool as UpdateInventoryTool, ForecastTool as ForecastInventoryTool
from tools.base_tool import _tool_registry

# Initialize the LLM and memory
llm = get_llm()
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Initialize the tools
# Instantiate concrete Tool callables bound to db_path
read_tool = ReadInventoryTool(str(DB_PATH))
write_tool = UpdateInventoryTool(str(DB_PATH))
forecast_tool = ForecastInventoryTool(str(DB_PATH))

from langchain_core.tools import Tool as LCTool

inventory_tools = [
    LCTool(name=read_tool.name, description=read_tool.description, func=read_tool._run),
    LCTool(name=write_tool.name, description=write_tool.description, func=write_tool._run),
    LCTool(name=forecast_tool.name, description=forecast_tool.description, func=forecast_tool._run),
]

# Define the agent's prompt with required variables
inventory_prompt_template = """
You are a specialized inventory management agent for an ERP system. Your goal is to manage stock levels, provide inventory forecasts, and answer questions about products.

You have access to the following tools:
{tools}

Format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

tool_strings = "\n".join([f"{t.name}: {t.description}" for t in inventory_tools])
tool_names = ", ".join([t.name for t in inventory_tools])
prompt = PromptTemplate(template=inventory_prompt_template, input_variables=["input","agent_scratchpad","tools","tool_names"]).partial(tools=tool_strings, tool_names=tool_names)

# Create the agent executor
inventory_executor = AgentExecutor(
    agent=create_react_agent(llm, inventory_tools, prompt),
    tools=inventory_tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)
