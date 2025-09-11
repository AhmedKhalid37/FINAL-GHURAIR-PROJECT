import sqlite3
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from ..config.llm import get_llm  # Corrected import for LLM
from ..tools.inventory_tools import (  # Corrected import for tools
    InventorySQLReadTool, 
    InventorySQLWriteTool, 
    ForecastTool, 
    DocRAGTool
)

class InventoryAgent:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.tools = [
            InventorySQLReadTool(db_path),
            InventorySQLWriteTool(db_path),
            ForecastTool(),
            DocRAGTool()
        ]
        self.memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history")
        self.agent = initialize_agent(
            tools=self.tools,
            llm=get_llm(),  # Corrected placeholder to use LLM
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=self.memory
        )

    def run(self, prompt: str):
        return self.agent.run(prompt)

# Example usage:
# inventory_agent = InventoryAgent('erp_sample.db')
# response = inventory_agent.run("Check stock level for product 'Laptop'")