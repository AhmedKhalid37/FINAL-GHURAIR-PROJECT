import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from ..config.llm import get_llm
from ..tools.analytics_tools import TextToSQLTool, RAGDefinitionTool, AnalyticsReportingTool

# Initialize the LLM and memory
llm = get_llm()
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Initialize the tools
analytics_tools = [
    TextToSQLTool(),
    RAGDefinitionTool(),
    AnalyticsReportingTool()
]

# Define the agent's prompt
analytics_prompt_template = """
You are a specialized analytics agent for an ERP system. Your goal is to answer questions about business data and generate reports. You have access to the following tools:
{tools}

Use these tools to answer the user's questions. You should always try to use the most specific tool for the task.

Begin!

Question: {input}
{agent_scratchpad}
"""

# Create the agent executor
analytics_executor = AgentExecutor(
    agent=create_react_agent(llm, analytics_tools, PromptTemplate.from_template(analytics_prompt_template)),
    tools=analytics_tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# You can still define a handler function if needed, but the executor is the main export
# def handle_analytics_query(query: str):
#     return analytics_executor.invoke({"input": query})
