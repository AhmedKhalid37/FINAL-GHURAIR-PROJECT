import pandas as pd
from langchain.agents import AgentExecutor, initialize_agent
from langchain.memory import ConversationBufferWindowMemory
from ..tools.analytics_tools import text_to_sql_tool, rag_definition_tool, analytics_reporting_tool
from ...config.llm import get_llm # <-- ADD THIS IMPORT

class AnalyticsAgent:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.tools = [
            text_to_sql_tool(db_path),
            rag_definition_tool(),
            analytics_reporting_tool()
        ]
        self.memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history")
        self.agent = initialize_agent(
            tools=self.tools,
            llm=get_llm(), # <-- CHANGE THIS LINE
            agent="zero-shot-react-description",
            verbose=True,
            memory=self.memory
        )

    def run(self, prompt: str):
        return self.agent.run(prompt)