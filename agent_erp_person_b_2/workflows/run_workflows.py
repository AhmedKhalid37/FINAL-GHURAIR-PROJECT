import os
from agents.sales.sales_agent import SalesAgent
from agents.finance.finance_agent import FinanceAgent

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "db", "erp_sample.db")

def ensure_db():
    if not os.path.exists(DB_PATH):
        from db.init_db import init
        init(DB_PATH, os.path.join(BASE, "db", "seed_data.sql"))

def print_step(title):
    print("\n" + "="*len(title))
    print(title)
    print("="*len(title))

def main():
    ensure_db()
    sales = SalesAgent(DB_PATH)
    finance = FinanceAgent(DB_PATH)

    print_step("1) Add Lead")
    r = sales.handle("add_lead", {"name":"Acme Buyer","email":"buyer@acme.test","source":"email","notes":"Interested to buy 10 panels"})
    print(r)
    lead_id = r.get("lead_id", 1)

    print_step("2) Lead Score (heuristic)")
    features = {"msg_len": 80, "kw_hits": 2, "visits": 3, "source": "email"}
    r = sales.handle("lead_score", {"features": features})
    print(r)

    print_step("3) Convert Lead to Order")
    r = sales.handle("convert_lead_to_order", {"lead_id": lead_id, "product_id": 1, "qty": 10})
    print(r)
    order_id = r.get("order_id")

    print_step("4) Generate Invoice From Order")
    r = finance.handle("generate_invoice_from_order", {"order_id": order_id})
    print(r)
    invoice_id = r.get("invoice_id")

    print_step("5) Detect Anomaly")
    r = finance.handle("detect_anomaly", {"invoice_id": invoice_id})
    print(r)

    print_step("6) Policy Lookup")
    r = finance.handle("policy_lookup", {"q": "approval", "k": 2})
    print(r)

if __name__ == "__main__":
    main()
