import sqlite3
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from tools.base_tool import BaseTool, register_tool


@register_tool
class InventorySQLReadTool(BaseTool):
    name = "inventory_sql_read"
    description = "Read data from inventory tables (stock, suppliers, products, etc.)."

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def _run(self, query: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            return {"error": str(e)}


@register_tool
class InventorySQLWriteTool(BaseTool):
    name = "inventory_sql_write"
    description = "Insert/update/delete data in inventory tables (stock, orders, receipts, etc.)."

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def _run(self, query: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            return {"status": "success"}
        except Exception as e:
            self.conn.rollback()
            return {"error": str(e)}


@register_tool
class ForecastTool(BaseTool):
    name = "forecast_tool"
    description = "Generate demand forecasts from historical stock movement data."

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def _run(self, product_id: str, periods: int = 12):
        query = f"""
            SELECT date, quantity
            FROM stock_movements
            WHERE product_id = '{product_id}'
            ORDER BY date
        """
        df = pd.read_sql_query(query, self.conn)

        if df.empty:
            return {"forecast": [], "message": "No historical data"}

        try:
            model = ExponentialSmoothing(df['quantity'], trend="add", seasonal=None)
            fit = model.fit()
            forecast = fit.forecast(periods).tolist()
            return {"product_id": product_id, "forecast": forecast}
        except Exception as e:
            return {"error": str(e)}


@register_tool
class DocRAGTool(BaseTool):
    name = "doc_rag_tool"
    description = "Retrieve supplier contracts, policies, or incident reports from internal documents."

    def _run(self, query: str):
        # For now just a stub — later connect this to embeddings + vector DB
        return {"result": f"Simulated doc lookup for: {query}"}
