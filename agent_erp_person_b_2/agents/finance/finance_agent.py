from typing import Dict, Any
from .finance_sql_tool import FinanceSQLTool
from .policy_rag_tool import PolicyRAGTool
from .anomaly_detector_tool import AnomalyDetectorTool

class FinanceAgent:
    def __init__(self, db_path: str):
        self.sql = FinanceSQLTool(db_path)
        self.rag = PolicyRAGTool(db_path)
        self.detector = AnomalyDetectorTool(db_path)
    def handle(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if intent == "policy_lookup":
            return self.rag.run({"query": data.get("q",""), "k": data.get("k",3)})
        if intent == "generate_invoice_from_order":
            order_id = int(data["order_id"])
            order = self.sql.run({"op":"read","query":"SELECT customer_id,total_amount,currency FROM orders WHERE order_id=?","params":[order_id]})
            if not order["ok"] or not order["rows"]:
                return {"ok": False, "error": "Order not found"}
            customer_id, total_amount, currency = order["rows"][0]
            vendor_id = 1
            ins = self.sql.run({"op":"write","query":"INSERT INTO invoices(vendor_id, invoice_no, date, currency, subtotal, tax, total, status, risk_score, created_at) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)","params":[vendor_id, f"INV-{order_id}", "2025-01-01", currency, total_amount, 0.0, total_amount, "posted", 0.0]})
            if not ins["ok"]:
                return ins
            invoice_id = ins.get("lastrowid")
            self.sql.run({"op":"write","query":"INSERT INTO invoice_lines(invoice_id, product_id, qty, unit_price, tax_rate) VALUES(?,?,?,?,?)","params":[invoice_id, None, 1, total_amount, 0.0]})
            self.sql.run({"op":"write","query":"INSERT INTO invoice_orders(invoice_id, order_id) VALUES(?,?)","params":[invoice_id, order_id]})
            return {"ok": True, "invoice_id": invoice_id, "total": total_amount}
        if intent == "detect_anomaly":
            if "invoice_id" in data:
                return self.detector.run({"invoice_id": int(data["invoice_id"])})
            return self.detector.run({"features": data.get("features", {})})
        return {"ok": False, "error": f"Unknown intent: {intent}"}
