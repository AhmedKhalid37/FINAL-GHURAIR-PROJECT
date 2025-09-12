import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from config.llm import get_llm
from config.database import get_db_schema, get_db_name
from tools.analytics_tools import TextToSQLTool

# Initialize the LLM and memory
llm = get_llm()
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

# Initialize the tools
from tools.analytics_tools import TextToSQLTool
from langchain_core.tools import Tool as LCTool

_text_sql = TextToSQLTool()
analytics_tools = [
    LCTool(name=_text_sql.name, description=_text_sql.description, func=_text_sql._run)
]

# Define the agent's prompt with required variables
analytics_prompt_template = """
You are a specialized analytics agent for an ERP system. Your goal is to answer questions about business data and generate reports.

Context:
- Database engine: SQLite
- Database name: {db_name}
- Database schema (tables and columns): {db_schema}

You have access to the following tools:
{tools}

CRITICAL INSTRUCTIONS:
- Always use the tools to answer questions; do not ask the user for database details.
- When asked analytics questions (e.g., revenue by month), write a valid SQLite SQL query and call text_to_sql_tool.
- Prefer GROUP BY for aggregations and use strftime('%Y-%m', date) for monthly grouping if needed.
- Return concise, human-friendly results.

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

tool_strings = "\n".join([f"{t.name}: {t.description}" for t in analytics_tools])
tool_names = ", ".join([t.name for t in analytics_tools])
db_schema = str(get_db_schema())
db_name = get_db_name()
prompt = PromptTemplate(
    template=analytics_prompt_template,
    input_variables=["input","agent_scratchpad","tools","tool_names","db_schema","db_name"]
).partial(tools=tool_strings, tool_names=tool_names, db_schema=db_schema, db_name=db_name)

# Create the agent executor
analytics_executor = AgentExecutor(
    agent=create_react_agent(llm, analytics_tools, prompt),
    tools=analytics_tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# You can still define a handler function if needed, but the executor is the main export
# def handle_analytics_query(query: str):
#     return analytics_executor.invoke({"input": query})
