from langchain.prompts import PromptTemplate

def import_get_react_prompt():
    """Get the ReAct prompt template for agents"""
    template = """You are a helpful AI assistant that can use tools to answer questions and perform tasks.

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    return PromptTemplate(
        template=template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )

def get_router_prompt():
    """Get prompt specifically for the router agent"""
    template = """You are a Smart Router Agent for an ERP system. Your job is to:

1. Classify user requests into appropriate domains (sales, finance, inventory, analytics)
2. Route requests to the correct specialized agent
3. Provide system information when requested
4. Handle approval workflows when needed

Available tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    return PromptTemplate(
        template=template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )
