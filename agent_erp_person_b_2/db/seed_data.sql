PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS customers (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, phone TEXT, segment TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS leads (lead_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, source TEXT, status TEXT, notes TEXT, score REAL, created_at TEXT);
CREATE TABLE IF NOT EXISTS products (product_id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, name TEXT, price REAL, stock_qty INTEGER DEFAULT 100);
CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER REFERENCES customers(customer_id), status TEXT, total_amount REAL, currency TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS order_items (item_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER REFERENCES orders(order_id), product_id INTEGER REFERENCES products(product_id), qty INTEGER, unit_price REAL);
CREATE TABLE IF NOT EXISTS tickets (ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER REFERENCES customers(customer_id), subject TEXT, status TEXT, last_msg_at TEXT);
CREATE TABLE IF NOT EXISTS documents (doc_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT, category TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS vendors (vendor_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);
CREATE TABLE IF NOT EXISTS invoices (invoice_id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id INTEGER REFERENCES vendors(vendor_id), invoice_no TEXT, date TEXT, currency TEXT, subtotal REAL, tax REAL, total REAL, status TEXT, risk_score REAL, created_at TEXT);
CREATE TABLE IF NOT EXISTS invoice_lines (line_id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER REFERENCES invoices(invoice_id), product_id INTEGER, qty REAL, unit_price REAL, tax_rate REAL);
CREATE TABLE IF NOT EXISTS invoice_orders (invoice_id INTEGER REFERENCES invoices(invoice_id), order_id INTEGER REFERENCES orders(order_id));
CREATE TABLE IF NOT EXISTS payments (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER REFERENCES invoices(invoice_id), amount REAL, method TEXT, paid_at TEXT);
CREATE TABLE IF NOT EXISTS payment_allocations (allocation_id INTEGER PRIMARY KEY AUTOINCREMENT, payment_id INTEGER REFERENCES payments(payment_id), invoice_id INTEGER REFERENCES invoices(invoice_id), amount REAL);
CREATE TABLE IF NOT EXISTS chart_of_accounts (account_code TEXT PRIMARY KEY, name TEXT, type TEXT);
CREATE TABLE IF NOT EXISTS ledger_entries (entry_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, description TEXT, total_debit REAL, total_credit REAL);
CREATE TABLE IF NOT EXISTS ledger_lines (line_id INTEGER PRIMARY KEY AUTOINCREMENT, entry_id INTEGER REFERENCES ledger_entries(entry_id), account_code TEXT REFERENCES chart_of_accounts(account_code), debit REAL, credit REAL);
CREATE TABLE IF NOT EXISTS approvals (approval_id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT, entity_id INTEGER, reason TEXT, level TEXT, status TEXT, requested_by TEXT, decided_by TEXT, decided_at TEXT);
INSERT OR IGNORE INTO products(sku,name,price,stock_qty) VALUES ('SKU-100','Solar Panel 200W',250.0,200),('SKU-101','Inverter 1.5kW',430.0,100),('SKU-102','Battery Pack 5kWh',900.0,50);
INSERT OR IGNORE INTO vendors(vendor_id, name) VALUES (1, 'Default Vendor');
INSERT OR IGNORE INTO documents(title, body, category, updated_at) VALUES
('Sales FAQ - Returns','Customers can return items within 14 days with receipt.','faq','2025-01-01'),
('Sales Manual - Order Creation','To create an order, you need a customer and at least one product.','manual','2025-01-01'),
('Finance Policy - Invoice Approval','Invoices above 10,000 USD require manager approval.','policy','2025-01-01'),
('Glossary - Ledger Entry','A ledger entry is a journal header with multiple lines.','glossary','2025-01-01');
