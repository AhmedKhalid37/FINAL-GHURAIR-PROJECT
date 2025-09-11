import json
import sqlite3
from typing import Any, List
from langchain.prompts import PromptTemplate
from langchain.agents import tool
from ..base_tool import BaseTool, register_tool
from ...config.llm import get_llm
from ...config.database import get_db_schema, execute_query
from ...helpers import get_db_name

DB_NAME = get_db_name()

@register_tool
class RAGDefinitionTool(BaseTool):
    name = "rag_definition_tool"
    description = "Provides definitions and explanations from a predefined knowledge base. Use this for general queries about ERP concepts or policies. Input should be a specific term or topic."

    def __init__(self):
        super().__init__()
        # In a real app, this would be a vector store search
        self.definitions = {
            "policy": "Policy 1: All sales over $5000 require manager approval.",
            "erp": "Enterprise Resource Planning (ERP) is a software system that integrates all aspects of an enterprise's operations.",
            "crm": "Customer Relationship Management (CRM) is a system for managing interactions with current and potential customers."
        }

    def run(self, query: str) -> str:
        """Retrieves and returns a definition from the internal knowledge base."""
        match = self.definitions.get(query.lower())
        if match:
            return f"Definition for '{query}': {match}"
        return "No definition found for that term."

@register_tool
class AnalyticsReportingTool(BaseTool):
    name = "analytics_reporting_tool"
    description = "Generates a predefined analytics report based on a query result. This tool can summarize data, identify trends, or create simple visual reports. Input should be a string describing the report needed."

    def __init__(self):
        super().__init__()
    
    def run(self, report_name: str) -> str:
        """Generates a sample report based on a predefined name."""
        if "monthly sales" in report_name.lower():
            # Example: Fetch data and format it into a report string
            data = execute_query("SELECT strftime('%Y-%m', created_at) AS month, SUM(total) FROM orders GROUP BY month;")
            report_summary = f"Monthly Sales Report:\n"
            for row in data:
                report_summary += f"- {row[0]}: ${row[1]:,.2f}\n"
            return report_summary
        return f"Report '{report_name}' not found."

@register_tool
class TextToSQLTool(BaseTool):
    name = "text_to_sql_tool"
    description = "Translates natural language questions into executable SQL queries for the ERP database. This tool is for answering questions about business data, not for making changes. Input should be a complete sentence."

    def __init__(self):
        super().__init__()
        self.llm = get_llm()
        self.schema = get_db_schema()

    def run(self, question: str) -> str:
        """
        Dynamically generates a SQL query based on the user's question and the database schema, then executes it.
        """
        schema_string = "\n".join([f"Table: {table}, Columns: {', '.join(cols)}" for table, cols in self.schema.items()])

        prompt_template = PromptTemplate.from_template(
            """You are a skilled data analyst. Your task is to convert a natural language question into a SQLite SQL query.
            The database name is '{db_name}' and has the following tables and columns:
            {schema}

            Your query should:
            - Be a valid SQLite query.
            - Only use columns that exist in the database schema.
            - Not use any other tools.
            - Return only the SQL query as a single line, and nothing else.
            
            Question: {question}
            SQL Query:"""
        )

        llm_input = prompt_template.format(db_name=DB_NAME, schema=schema_string, question=question)

        try:
            sql_query = self.llm.invoke(llm_input).content.strip()
            # It's crucial to only allow SELECT queries to prevent data manipulation
            if not sql_query.lower().startswith("select"):
                return "Only SELECT queries are allowed."
            
            result = execute_query(sql_query)
            return f"Successfully executed query. Result: {json.dumps(result)}"
        except Exception as e:
            return f"An error occurred while generating or executing the SQL query: {e}"