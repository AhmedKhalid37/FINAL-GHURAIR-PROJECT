from typing import Dict, Any
from .sales_sql_tool import SalesSQLTool
from .sales_rag_tool import SalesRAGTool
from .lead_score_tool import LeadScoreTool

class SalesAgent:
    def __init__(self, db_path: str, lead_model_path: str = None):
        self.sql = SalesSQLTool(db_path)
        self.rag = SalesRAGTool(db_path)
        self.scorer = LeadScoreTool(lead_model_path)
    def handle(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if intent == "add_lead":
            q = """INSERT INTO leads(name,email,source,status,notes,created_at)
                   VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)"""
            p = [data["name"], data["email"], data.get("source","web"),
                 "new", data.get("notes","")]
            ins = self.sql.run({"op":"write","query":q,"params":p})
            if not ins["ok"]:
                return ins
            return {"ok": True, "lead_id": ins.get("lastrowid")}
        if intent == "lead_score":
            return self.scorer.run({"features": data.get("features", {})})
        if intent == "convert_lead_to_order":
            lead_id = int(data["lead_id"])
            product_id = int(data["product_id"])
            qty = int(data.get("qty", 1))
            r = self.sql.run({"op":"read","query":"SELECT name, email FROM leads WHERE lead_id=?","params":[lead_id]})
            if not r["ok"] or not r["rows"]:
                return {"ok": False, "error": "Lead not found"}
            name, email = r["rows"][0]
            r2 = self.sql.run({"op":"read","query":"SELECT customer_id FROM customers WHERE email=?","params":[email]})
            if r2["ok"] and r2["rows"]:
                customer_id = r2["rows"][0][0]
            else:
                ins = self.sql.run({"op":"write","query":"INSERT INTO customers(name,email,created_at) VALUES(?, ?, CURRENT_TIMESTAMP)","params":[name, email]})
                if not ins["ok"]:
                    return ins
                customer_id = ins.get("lastrowid")
            ins_o = self.sql.run({"op":"write","query":"INSERT INTO orders(customer_id,status,total_amount,currency,created_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)","params":[customer_id, "draft", 0.0, "USD"]})
            if not ins_o["ok"]:
                return ins_o
            order_id = ins_o.get("lastrowid")
            pr = self.sql.run({"op":"read","query":"SELECT price FROM products WHERE product_id=?","params":[product_id]})
            if not pr["ok"] or not pr["rows"]:
                return {"ok": False, "error": "Product not found"}
            price = float(pr["rows"][0][0])
            self.sql.run({"op":"write","query":"INSERT INTO order_items(order_id,product_id,qty,unit_price) VALUES(?,?,?,?)","params":[order_id, product_id, qty, price]})
            total = price * qty
            self.sql.run({"op":"write","query":"UPDATE orders SET total_amount=?, status='open' WHERE order_id=?","params":[total, order_id]})
            self.sql.run({"op":"write","query":"UPDATE leads SET status='converted' WHERE lead_id=?","params":[lead_id]})
            return {"ok": True, "order_id": order_id, "customer_id": customer_id, "total": total}
        if intent == "search_docs":
            return self.rag.run({"query": data.get("q",""), "k": data.get("k", 3)})
        return {"ok": False, "error": f"Unknown intent: {intent}"}
