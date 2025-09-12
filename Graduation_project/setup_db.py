# setup_db.py - Build and seed the minimal erp_sample.db for the Router Agent demo

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "erp_sample.db"


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Core ERP tables
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            email TEXT,
            phone TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            sku TEXT,
            price REAL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_id INTEGER,
            total REAL,
            status TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            order_id INTEGER,
            amount REAL,
            status TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            source TEXT,
            status TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            product_id INTEGER,
            quantity INTEGER,
            warehouse TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """
    )

    # Orchestrator tables
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            user_input TEXT,
            agent_output TEXT,
            agent TEXT,
            success INTEGER
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            agent TEXT,
            inputs TEXT,
            outputs TEXT,
            success INTEGER
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            user_id TEXT,
            request TEXT,
            agent TEXT,
            status TEXT,
            reasons TEXT
        );
        """
    )

    # Seed data (idempotent simple checks)
    cur.execute("SELECT COUNT(1) FROM customers")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
            [
                ("Alice Corp", "alice@example.com", "+1-555-1001"),
                ("Bob LLC", "bob@example.com", "+1-555-1002"),
            ],
        )

    cur.execute("SELECT COUNT(1) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products (name, sku, price) VALUES (?, ?, ?)",
            [
                ("Widget A", "WID-A", 19.99),
                ("Widget B", "WID-B", 29.99),
            ],
        )

    cur.execute("SELECT COUNT(1) FROM orders")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO orders (customer_id, total, status) VALUES (?, ?, ?)",
            [
                (1, 49.98, "PAID"),
                (2, 19.99, "PENDING"),
            ],
        )

    cur.execute("SELECT COUNT(1) FROM invoices")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO invoices (order_id, amount, status) VALUES (?, ?, ?)",
            [
                (1, 49.98, "SENT"),
                (2, 19.99, "DRAFT"),
            ],
        )

    cur.execute("SELECT COUNT(1) FROM leads")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO leads (name, source, status) VALUES (?, ?, ?)",
            [
                ("Charlie", "Website", "New"),
                ("Diane", "Referral", "Contacted"),
            ],
        )

    cur.execute("SELECT COUNT(1) FROM stock")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO stock (product_id, quantity, warehouse) VALUES (?, ?, ?)",
            [
                (1, 100, "WH-1"),
                (2, 50, "WH-2"),
            ],
        )

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    run() 