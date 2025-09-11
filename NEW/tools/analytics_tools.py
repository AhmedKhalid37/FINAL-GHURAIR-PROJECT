import json
import sqlite3
from typing import Dict, List, Type # Import Type
from pydantic import BaseModel, Field
from langchain.tools import Tool

from tools.base_tool import BaseTool, register_tool
from config.database import get_db_schema, get_db_name, get_connection

# Input schema for TextToSQLTool
class TextToSQLToolInput(BaseModel):
    query: str = Field(description="A detailed SQL query to execute against the database.")

@register_tool
class TextToSQLTool(BaseTool):
    name: str = "text_to_sql_tool"
    description: str = """
    A tool to convert natural language questions into executable SQL queries and run them.
    This tool requires a well-formed SQL query as input. It can read from all available tables.
    The database schema is as follows:
    - customers(customer_id, name, email, country)
    - products(product_id, name, category, price, stock)
    - sales(sale_id, customer_id, product_id, date, quantity, total)
    - vendors(vendor_id, name, email)
    - invoices(invoice_id, vendor_id, amount, due_date, status)
    - invoice_lines(id, invoice_id, product_id, qty, unit_price)
    - orders(order_id, customer_id, date, status)
    - order_items(id, order_id, product_id, qty, unit_price)
    
    You must always provide a complete SQL query as input.
    """
    # CORRECTED THIS LINE 👇
    args_schema: Type[BaseModel] = TextToSQLToolInput

    def _run(self, query: str):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            # To handle cases with no results
            if not rows:
                return "Query executed successfully, but no results were found."
            return f"Query executed successfully. Results: {rows}"
        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            return f"An error occurred while executing the query: {e}"
        finally:
            if conn:
                conn.close()