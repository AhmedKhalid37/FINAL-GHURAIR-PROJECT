import sqlite3
from pathlib import Path
from .config.database import DB_PATH

def create_initial_tables(conn: sqlite3.Connection):
    """
    Creates the necessary tables for the ERP system with comprehensive schemas.
    """
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            price REAL NOT NULL,
            stock_level INTEGER NOT NULL,
            unit_of_measure TEXT
        );
    """)

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            address TEXT
        );
    """)

    # Vendors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT
        );
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)
    
    # Order items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)

    # Invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
    """)

    # Invoice lines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_lines (
            id INTEGER PRIMARY KEY,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)

    # Add sample data
    cursor.execute("INSERT OR REPLACE INTO products (product_id, name, description, category, price, stock_level, unit_of_measure) VALUES (1, 'Laptop', 'High performance laptop', 'Electronics', 1200.00, 50, 'units');")
    cursor.execute("INSERT OR REPLACE INTO products (product_id, name, description, category, price, stock_level, unit_of_measure) VALUES (2, 'Mouse', 'Wireless ergonomic mouse', 'Electronics', 25.00, 200, 'units');")
    cursor.execute("INSERT OR REPLACE INTO customers (customer_id, first_name, last_name, email) VALUES (1, 'John', 'Doe', 'john.doe@example.com');")
    cursor.execute("INSERT OR REPLACE INTO vendors (vendor_id, name, contact_person, email) VALUES (1, 'Tech Supplies Inc.', 'Jane Smith', 'jane.smith@techsupplies.com');")
    
    conn.commit()

def setup_database():
    """
    Initializes the SQLite database and populates it with tables and sample data.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    create_initial_tables(conn)
    conn.close()
    print(f"Database setup complete at {DB_PATH}")

if __name__ == "__main__":
    setup_database()
