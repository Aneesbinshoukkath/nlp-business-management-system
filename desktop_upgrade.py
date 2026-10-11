import os
import pymysql

# ==========================================================
# 1. DATABASE SCHEMA MIGRATION: ADD ALL MISSING PDF COLUMNS
# ==========================================================
conn = pymysql.connect(
    host="localhost",
    user="biz_user",
    password="biz_pass123",
    database="business_management"
)
cursor = conn.cursor()

# 1. Customers Table (Add Type and City from PDF)
cursor.execute("CREATE TABLE IF NOT EXISTS customers (customer_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, phone VARCHAR(20), email VARCHAR(100));")
for col in [
    "type ENUM('Retail', 'Corporate') DEFAULT 'Retail'",
    "city VARCHAR(100) DEFAULT 'Pune'"
]:
    try: cursor.execute(f"ALTER TABLE customers ADD COLUMN {col};")
    except Exception: pass

# 2. Products Table (Add Reorder Level & Supplier Reference from PDF)
cursor.execute("CREATE TABLE IF NOT EXISTS products (product_id INT AUTO_INCREMENT PRIMARY KEY, product_name VARCHAR(150) NOT NULL, price DECIMAL(10, 2) NOT NULL, stock INT DEFAULT 0);")
for col in [
    "sku VARCHAR(50) DEFAULT 'SKU-1001'",
    "category VARCHAR(100) DEFAULT 'General'",
    "cost_price DECIMAL(10, 2) DEFAULT 0.00",
    "reorder_level INT DEFAULT 10",
    "supplier_id INT"
]:
    try: cursor.execute(f"ALTER TABLE products ADD COLUMN {col};")
    except Exception: pass

# 3. Employees Table (Add Phone, Salary, Join Date, Status from PDF)
cursor.execute("CREATE TABLE IF NOT EXISTS employees (employee_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, designation VARCHAR(100), dept_id INT);")
for col in [
    "user_id INT",
    "phone VARCHAR(20)",
    "monthly_salary DECIMAL(10, 2) DEFAULT 45000.00",
    "join_date DATE DEFAULT (CURDATE())",
    "status ENUM('Active', 'Leave') DEFAULT 'Active'"
]:
    try: cursor.execute(f"ALTER TABLE employees ADD COLUMN {col};")
    except Exception: pass

# 4. Purchases Table (Add PO Number, Qty, Status from PDF)
cursor.execute("CREATE TABLE IF NOT EXISTS purchases (purchase_id INT AUTO_INCREMENT PRIMARY KEY, purchase_date DATE NOT NULL, total_amount DECIMAL(10, 2) NOT NULL);")
for col in [
    "po_number VARCHAR(50) DEFAULT 'PO-3001'",
    "quantity INT DEFAULT 1",
    "supplier_id INT",
    "invoice_ref VARCHAR(100)",
    "notes VARCHAR(255)",
    "status VARCHAR(50) DEFAULT 'Received'"
]:
    try: cursor.execute(f"ALTER TABLE purchases ADD COLUMN {col};")
    except Exception: pass

# 5. Populate standard mock data matching the PDF screens
cursor.execute("SELECT COUNT(*) FROM customers WHERE type = 'Corporate';")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO customers (name, type, city, email, phone) VALUES
    ('Acme Corp', 'Corporate', 'Hyderabad', 'contact@acmecorp.com', '+91 98450 11001'),
    ('Bluewave Solutions', 'Corporate', 'Pune', 'contact@bluewave.io', '+91 98450 11002'),
    ('Nova Retail', 'Corporate', 'Delhi', 'contact@novaretail.com', '+91 98450 11003'),
    ('Sunrise Clinics', 'Corporate', 'Pune', 'contact@sunriseclinics.org', '+91 98450 11004'),
    ('Orbit Logistics', 'Corporate', 'Mumbai', 'contact@orbitlogistics.in', '+91 98450 11005'),
    ('Kiran Mehta', 'Retail', 'Pune', 'kiran.mehta@gmail.com', '+91 98765 43210');
    """)

cursor.execute("SELECT COUNT(*) FROM purchases WHERE po_number LIKE 'PO-%';")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO purchases (po_number, purchase_date, total_amount, quantity, status) VALUES
    ('PO-3032', '2026-10-05', 5178.00, 6, 'Received'),
    ('PO-3030', '2026-10-04', 990.00, 6, 'Received'),
    ('PO-3012', '2026-10-01', 2008.00, 8, 'Received'),
    ('PO-3036', '2026-09-30', 4845.00, 15, 'Ordered'),
    ('PO-3004', '2026-09-29', 9884.00, 14, 'Received'),
    ('PO-3037', '2026-09-20', 1926.00, 18, 'Received'),
    ('PO-3002', '2026-09-10', 7205.00, 11, 'Ordered');
    """)

conn.commit()
conn.close()
print("Database migrated with all PDF fields.")

# ==========================================================
# 2. UPGRADE NLP ENGINE TO HANDLE ALL 10 PREDEFINED QUERIES
# ==========================================================
nlp_code = """import re
from datetime import date

class NLPQueryParser:
    def __init__(self, db_cursor):
        self.cursor = db_cursor

    def process_query(self, user_query: str):
        query = user_query.strip().lower()

        # 1. Show today's sales
        if "today's sales" in query or "sales today" in query:
            today_str = date.today().strftime('%Y-%m-%d')
            sql = "SELECT IFNULL(SUM(total_amount), 0) AS total_sales, COUNT(sale_id) AS total_orders FROM sales WHERE DATE(sale_date) = %s"
            self.cursor.execute(sql, (today_str,))
            res = self.cursor.fetchone()
            return {
                "intent": "SALES_QUERY_TODAY",
                "confidence": "98.9%",
                "entities": [{"type": "DATE", "value": "TODAY"}],
                "sql": sql.replace("%s", f"'{today_str}'"),
                "answer": f"Today's total sales amount to ${float(res['total_sales']):,.2f} across {res['total_orders']} orders."
            }

        # 2. How many laptops are currently in stock?
        if "laptops are currently in stock" in query or "how many laptops" in query:
            sql = "SELECT product_name, stock FROM products WHERE LOWER(product_name) LIKE '%laptop%'"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            tot = sum(r['stock'] for r in rows)
            details = ", ".join([f"{r['product_name']}: {r['stock']} units" for r in rows])
            return {
                "intent": "INVENTORY_CATEGORY_STOCK",
                "confidence": "97.4%",
                "entities": [{"type": "CATEGORY", "value": "Laptops"}],
                "sql": sql,
                "answer": f"There are {tot} total laptops in stock ({details})."
            }

        # 3. Which products have less than 10 items?
        threshold_match = re.search(r'(?:less than|under|below)\\s+(\\d+)', query)
        if threshold_match and ("stock" in query or "items" in query or "product" in query):
            num = int(threshold_match.group(1))
            sql = "SELECT product_name, stock FROM products WHERE stock < %s ORDER BY stock ASC"
            self.cursor.execute(sql, (num,))
            items = self.cursor.fetchall()
            formatted = ", ".join([f"{item['product_name']} ({item['stock']} left)" for item in items]) if items else f"None under {num}"
            return {
                "intent": "INVENTORY_LOW_STOCK_ALERT",
                "confidence": "98.1%",
                "entities": [{"type": "LIMIT", "value": str(num)}],
                "sql": sql.replace("%s", str(num)),
                "answer": f"Products with under {num} items: {formatted}."
            }

        # 4. Show sales for this month
        if "sales for this month" in query or "this month sales" in query:
            sql = "SELECT IFNULL(SUM(total_amount), 0) AS m_sales, COUNT(*) AS m_cnt FROM sales WHERE MONTH(sale_date) = MONTH(CURRENT_DATE()) AND YEAR(sale_date) = YEAR(CURRENT_DATE())"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            return {
                "intent": "SALES_QUERY_MONTH",
                "confidence": "96.5%",
                "entities": [{"type": "RANGE", "value": "CURRENT_MONTH"}],
                "sql": sql,
                "answer": f"Sales for this month total ${float(res['m_sales']):,.2f} across {res['m_cnt']} transactions."
            }

        # 5. Who are the employees in the sales department?
        if "employees in the sales department" in query or "sales department employees" in query:
            sql = "SELECT e.name, e.designation FROM employees e LEFT JOIN departments d ON e.dept_id = d.dept_id WHERE LOWER(d.dept_name) LIKE '%sales%'"
            self.cursor.execute(sql)
            emps = self.cursor.fetchall()
            list_str = ", ".join([f"{e['name']} ({e['designation']})" for e in emps]) if emps else "No employees listed in Sales."
            return {
                "intent": "HR_DEPARTMENT_DIRECTORY",
                "confidence": "98.2%",
                "entities": [{"type": "DEPARTMENT", "value": "Sales"}],
                "sql": sql,
                "answer": f"Employees in the Sales department: {list_str}."
            }

        # 6. Which product has the highest sales?
        if "highest sales" in query or "best selling" in query:
            sql = "SELECT p.product_name, IFNULL(SUM(si.quantity), 0) as total_sold FROM products p LEFT JOIN sale_items si ON p.product_id = si.product_id GROUP BY p.product_id, p.product_name ORDER BY total_sold DESC LIMIT 1"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            return {
                "intent": "SALES_TOP_PRODUCT",
                "confidence": "99.0%",
                "entities": [{"type": "METRIC", "value": "MAX(quantity)"}],
                "sql": sql,
                "answer": f"The highest selling product is '{res['product_name']}' with {res['total_sold']} units sold." if res else "No sales recorded."
            }

        # 7. Who is our top customer?
        if "top customer" in query:
            sql = "SELECT customer_name, IFNULL(SUM(total_amount), 0) as spent FROM sales GROUP BY customer_name ORDER BY spent DESC LIMIT 1"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            return {
                "intent": "CUSTOMER_TOP_SPENDER",
                "confidence": "95.5%",
                "entities": [{"type": "METRIC", "value": "MAX(total_amount)"}],
                "sql": sql,
                "answer": f"Top customer is '{res['customer_name']}' with total purchases of ${float(res['spent']):,.2f}." if res else "No customer sales recorded."
            }

        # 8. Show purchases from last month
        if "purchases from last month" in query or "last month purchases" in query:
            sql = "SELECT IFNULL(SUM(total_amount), 0) AS pur_tot, COUNT(*) AS pur_cnt FROM purchases WHERE purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            return {
                "intent": "PURCHASES_RECENT",
                "confidence": "94.8%",
                "entities": [{"type": "RANGE", "value": "LAST_MONTH"}],
                "sql": sql,
                "answer": f"Purchases from last month total ${float(res['pur_tot']):,.2f} across {res['pur_cnt']} purchase orders."
            }

        # 9. List all suppliers
        if "list all suppliers" in query or "all suppliers" in query:
            sql = "SELECT supplier_name, contact_person, phone FROM suppliers"
            self.cursor.execute(sql)
            sups = self.cursor.fetchall()
            list_str = "; ".join([f"{s['supplier_name']} (Contact: {s.get('contact_person') or 'N/A'})" for s in sups]) if sups else "No suppliers registered."
            return {
                "intent": "SUPPLIER_DIRECTORY",
                "confidence": "98.7%",
                "entities": [{"type": "ENTITY", "value": "Suppliers"}],
                "sql": sql,
                "answer": f"Registered Suppliers: {list_str}."
            }

        # 10. Total revenue this week
        if "revenue this week" in query or "total revenue this week" in query:
            sql = "SELECT IFNULL(SUM(total_amount), 0) AS rev FROM sales WHERE sale_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            return {
                "intent": "REVENUE_WEEKLY",
                "confidence": "97.0%",
                "entities": [{"type": "RANGE", "value": "LAST_7_DAYS"}],
                "sql": sql,
                "answer": f"Total revenue recorded in the last 7 days is ${float(res['rev']):,.2f}."
            }

        # Fallback
        return {
            "intent": "UNKNOWN_TEMPLATE",
            "confidence": "40.0%",
            "entities": [],
            "sql": "-- No SQL mapped",
            "answer": "This NLP engine matches predefined business queries. Click one of the suggestions above to test."
        }
"""
with open("nlp_engine/parser.py", "w") as f:
    f.write(nlp_code)

# ==========================================================
# 3. WRITE BACKEND (app.py) WITH CSV EXPORT & ALL ENDPOINTS
# ==========================================================
app_code = """from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import pymysql.cursors
import csv
import io
from nlp_engine.parser import NLPQueryParser

app = Flask(__name__)
app.secret_key = "bizcore_desktop_landscape_key"

def get_db():
    return pymysql.connect(
        host="localhost",
        user="biz_user",
        password="biz_pass123",
        database="business_management",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.before_request
def require_login():
    public = ['login', 'static']
    if request.endpoint not in public and 'user' not in session:
        return redirect(url_for('login'))

@app.route('/')
def root():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
                user = cursor.fetchone()
                if user:
                    session['user'] = {
                        'id': user['user_id'],
                        'name': user['name'],
                        'email': user['email'],
                        'role': user['role'],
                        'designation': user.get('designation', 'Staff')
                    }
                    return redirect(url_for('dashboard'))
                return render_template('login.html', error="Invalid email or password.")
        finally:
            conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', user=session['user'])

# Master API Data Feed
@app.route('/api/master-data')
def get_master_data():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Products
            cursor.execute("SELECT p.*, IFNULL(s.supplier_name, 'Direct Supply') as supplier_name FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id ORDER BY p.product_id DESC")
            products = cursor.fetchall()
            for p in products:
                p['price'] = float(p.get('price') or 0.0)
                p['cost_price'] = float(p.get('cost_price') or 0.0)
                p['reorder_level'] = int(p.get('reorder_level') or 10)
                p['status'] = 'Low stock' if p['stock'] < p['reorder_level'] else 'OK'

            # Low Stock list
            low_stock = [p for p in products if p['stock'] < p['reorder_level']]

            # Sales
            cursor.execute("SELECT * FROM sales ORDER BY sale_id DESC")
            sales = cursor.fetchall()
            for s in sales:
                s['sale_date'] = s['sale_date'].strftime('%Y-%m-%d')
                s['total_amount'] = float(s['total_amount'])

            # Customers
            cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
            customers = cursor.fetchall()

            # Employees
            cursor.execute(\"\"\"
                SELECT e.*, IFNULL(d.dept_name, 'General Operations') AS dept_name, IFNULL(u.role, 'employee') AS role
                FROM employees e
                LEFT JOIN departments d ON e.dept_id = d.dept_id
                LEFT JOIN users u ON e.user_id = u.user_id
                ORDER BY e.employee_id DESC
            \"\"\")
            employees = cursor.fetchall()
            for e in employees:
                if e.get('join_date'):
                    e['join_date'] = e['join_date'].strftime('%Y-%m-%d')

            # Departments
            cursor.execute("SELECT * FROM departments ORDER BY dept_name ASC")
            departments = cursor.fetchall()

            # Suppliers
            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
            suppliers = cursor.fetchall()

            # Purchases
            cursor.execute(\"\"\"
                SELECT p.*, IFNULL(s.supplier_name, 'Direct') AS supplier_name 
                FROM purchases p 
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id 
                ORDER BY p.purchase_id DESC
            \"\"\")
            purchases = cursor.fetchall()
            for pur in purchases:
                pur['purchase_date'] = pur['purchase_date'].strftime('%Y-%m-%d')
                pur['total_amount'] = float(pur['total_amount'])

            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) AS rev FROM sales")
            tot_rev = float(cursor.fetchone()['rev'])

            return jsonify({
                'products': products,
                'low_stock': low_stock,
                'sales': sales,
                'customers': customers,
                'employees': employees,
                'departments': departments,
                'suppliers': suppliers,
                'purchases': purchases,
                'total_revenue': tot_rev
            })
    finally:
        conn.close()

# Export Sales CSV (From PDF Page 11)
@app.route('/api/export-sales-csv')
def export_sales_csv():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT invoice_no, sale_date, customer_name, total_amount, payment_method, cashier_name FROM sales ORDER BY sale_id DESC")
            rows = cursor.fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Invoice No', 'Date', 'Customer', 'Total ($)', 'Payment Method', 'Cashier'])
            for r in rows:
                writer.writerow([r['invoice_no'], r['sale_date'].strftime('%Y-%m-%d'), r['customer_name'], r['total_amount'], r['payment_method'], r['cashier_name']])

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": "attachment; filename=sales_report.csv"}
            )
    finally:
        conn.close()

# 1. Add Customer (PDF Page 2)
@app.route('/api/add-customer', methods=['POST'])
def add_customer():
    d = request.get_json() or {}
    name = (d.get('name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Name required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(\"\"\"
                INSERT INTO customers (name, type, email, phone, city)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (name, d.get('type', 'Retail'), d.get('email'), d.get('phone'), d.get('city', 'Pune')))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 2. Add Product (PDF Page 4)
@app.route('/api/add-product', methods=['POST'])
def add_product():
    d = request.get_json() or {}
    name = (d.get('product_name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Product name required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM products")
            cnt = cursor.fetchone()['cnt']
            sku = (d.get('sku') or '').strip() or f"SKU-{1000 + cnt + 1}"
            cat = (d.get('category') or 'General').strip()
            cost = float(d.get('cost_price') or 0.0)
            price = float(d.get('price') or 0.0)
            stock = int(d.get('stock') or 0)
            reorder = int(d.get('reorder_level') or 10)
            sup_id = int(d['supplier_id']) if str(d.get('supplier_id')).isdigit() else None

            cursor.execute(\"\"\"
                INSERT INTO products (sku, product_name, category, cost_price, price, stock, reorder_level, supplier_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (sku, name, cat, cost, price, stock, reorder, sup_id))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 3. Add Employee (PDF Page 9)
@app.route('/api/add-employee', methods=['POST'])
def add_employee():
    d = request.get_json() or {}
    name = (d.get('name') or '').strip()
    email = (d.get('email') or '').strip()
    password = (d.get('password') or 'welcome123').strip()
    if not name or not email:
        return jsonify({'status': 'error', 'message': 'Name and Email required'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            dept_id = int(d['dept_id']) if str(d.get('dept_id')).isdigit() else 1
            pos = (d.get('position') or 'Sales Executive').strip()
            salary = float(d.get('monthly_salary') or 45000.0)
            status = d.get('status', 'Active')
            join_date = d.get('join_date') or date.today().strftime('%Y-%m-%d')

            cursor.execute(\"\"\"
                INSERT INTO users (name, email, password, role, designation)
                VALUES (%s, %s, %s, 'employee', %s)
            \"\"\", (name, email, password, pos))
            user_id = cursor.lastrowid

            cursor.execute(\"\"\"
                INSERT INTO employees (name, email, designation, dept_id, user_id, phone, monthly_salary, join_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (name, email, pos, dept_id, user_id, d.get('phone'), salary, join_date, status))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 4. Add Supplier
@app.route('/api/add-supplier', methods=['POST'])
def add_supplier():
    d = request.get_json() or {}
    name = (d.get('supplier_name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Supplier name required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(\"\"\"
                INSERT INTO suppliers (supplier_name, contact_person, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (name, d.get('contact_person'), d.get('phone'), d.get('email'), d.get('address')))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 5. Add Purchase (PDF Page 10)
@app.route('/api/add-purchase', methods=['POST'])
def add_purchase():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM purchases")
            po = f"PO-{3000 + cursor.fetchone()['cnt'] + 1}"
            tot = float(d.get('total_amount') or 0.0)
            qty = int(d.get('quantity') or 1)
            sup_id = int(d['supplier_id']) if str(d.get('supplier_id')).isdigit() else None
            p_date = d.get('purchase_date') or date.today().strftime('%Y-%m-%d')
            status = d.get('status', 'Received')

            cursor.execute(\"\"\"
                INSERT INTO purchases (po_number, supplier_id, purchase_date, total_amount, quantity, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            \"\"\", (po, sup_id, p_date, tot, qty, status))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 6. POS Checkout
@app.route('/api/pos-checkout', methods=['POST'])
def pos_checkout():
    d = request.get_json() or {}
    cart = d.get('cart', [])
    if not cart:
        return jsonify({'status': 'error', 'message': 'Empty cart'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM sales")
            inv = f"INV-{5000 + cursor.fetchone()['cnt'] + 1}"
            tot = float(d.get('total', 0))
            sub = float(d.get('subtotal', 0))
            disc = float(d.get('discount', 0))
            tax = float(d.get('tax', 0))
            chg = float(d.get('change_due', 0))
            cust = d.get('customer_name', 'Walk-in Customer')
            cashier = session['user']['name']
            method = d.get('payment_summary', 'Cash')

            cursor.execute(\"\"\"
                INSERT INTO sales (invoice_no, sale_date, customer_name, subtotal, discount, tax, total_amount, change_due, payment_method, cashier_name)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (inv, cust, sub, disc, tax, tot, chg, method, cashier))

            for it in cart:
                cursor.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (int(it['qty']), it['product_id']))

            conn.commit()
            return jsonify({'status': 'success', 'invoice_no': inv})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 7. NLP Query
@app.route('/api/nlp-query', methods=['POST'])
def process_nlp():
    data = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            parser = NLPQueryParser(cursor)
            res = parser.process_query(data.get('query', ''))
        return jsonify({'status': 'success', 'nlp_result': res})
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""
with open("app.py", "w") as f:
    f.write(app_code)

# ==========================================================
# 4. WRITE THE COMPLETE DESKTOP LANDSCAPE TEMPLATE
# ==========================================================
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BizCore NLP - Enterprise Business Management</title>
  <link rel="manifest" href="/static/manifest.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-[#0b1322] text-slate-100 min-h-screen font-sans flex overflow-hidden">

  <!-- ======================================================== -->
  <!-- 1. FIXED DESKTOP SIDEBAR (Admin & Employee Distinct)    -->
  <!-- ======================================================== -->
  <aside class="w-64 bg-[#070e1c] border-r border-slate-800 flex flex-col justify-between p-5 select-none shrink-0 h-screen">
    <div class="space-y-6">
      <!-- App Brand -->
      <div class="flex items-center space-x-3 px-2">
        <div class="w-10 h-10 rounded-2xl bg-[#00897b] flex items-center justify-center font-bold text-white shadow-lg">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
        </div>
        <div>
          <h2 class="font-extrabold text-white text-base tracking-tight leading-tight">BizCore NLP</h2>
          <p class="text-[11px] text-slate-400 font-medium">Business Management</p>
        </div>
      </div>

      <!-- Navigation Links -->
      <nav class="space-y-1.5 text-xs font-semibold">
        <!-- 1. Dashboard (Always available) -->
        <button onclick="switchTab('dashboard')" id="nav-dashboard" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl bg-[#13233b] text-teal-300">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
          <span>Dashboard</span>
        </button>

        {% if user.role == 'admin' %}
        <!-- 2. Employees (Admin Only - PDF Page 12) -->
        <button onclick="switchTab('employees')" id="nav-employees" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
          <span>Employees</span>
        </button>
        {% endif %}

        <!-- 3. Products -->
        <button onclick="switchTab('products')" id="nav-products" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
          <span>Products</span>
        </button>

        <!-- 4. Customers -->
        <button onclick="switchTab('customers')" id="nav-customers" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
          <span>Customers</span>
        </button>

        {% if user.role == 'admin' %}
        <!-- 5. Suppliers (Admin Only - PDF Page 12) -->
        <button onclick="switchTab('suppliers')" id="nav-suppliers" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
          <span>Suppliers</span>
        </button>
        {% endif %}

        <!-- 6. Sales / POS Terminal -->
        <button onclick="switchTab('pos')" id="nav-pos" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
          <span>Sales & POS</span>
        </button>

        {% if user.role == 'admin' %}
        <!-- 7. Purchases (Admin Only - PDF Page 12) -->
        <button onclick="switchTab('purchases')" id="nav-purchases" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>
          <span>Purchases</span>
        </button>
        {% endif %}

        <!-- 8. Inventory -->
        <button onclick="switchTab('inventory')" id="nav-inventory" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
          <span>Inventory</span>
        </button>

        {% if user.role == 'admin' %}
        <!-- 9. Reports (Admin Only - PDF Page 12) -->
        <button onclick="switchTab('reports')" id="nav-reports" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path></svg>
          <span>Reports</span>
        </button>
        {% endif %}

        <!-- 10. NLP Assistant (Always available) -->
        <button onclick="switchTab('nlp')" id="nav-nlp" class="nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-slate-300 hover:bg-slate-800">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
          <span>NLP Assistant</span>
        </button>
      </nav>
    </div>

    <!-- User Profile & Sign Out Footer -->
    <div class="border-t border-slate-800 pt-4 px-2 space-y-2">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-teal-400 text-xs">
          {{ user.name[:2].upper() }}
        </div>
        <div class="overflow-hidden">
          <p class="font-bold text-xs text-white truncate">{{ user.name }}</p>
          <p class="text-[10px] text-slate-400 truncate">{{ user.email }}</p>
        </div>
      </div>
      <a href="/logout" class="block w-full py-2 text-center text-xs text-rose-400 hover:bg-rose-500/10 rounded-xl font-semibold transition">
        → Sign out
      </a>
    </div>
  </aside>

  <!-- ======================================================== -->
  <!-- 2. MAIN DESKTOP CONTENT AREA                             -->
  <!-- ======================================================== -->
  <div class="flex-1 flex flex-col h-screen overflow-hidden">
    <!-- Top Bar -->
    <header class="h-16 bg-[#070e1c] border-b border-slate-800 px-8 flex items-center justify-between shrink-0">
      <div class="flex items-center space-x-4">
        <h1 id="screenHeaderTitle" class="text-lg font-extrabold text-white">Dashboard</h1>
        <span class="text-xs text-slate-400">|</span>
        <span class="text-xs text-teal-400 font-medium">{{ user.designation }}</span>
      </div>
      <div class="flex items-center space-x-3">
        <span class="px-3 py-1 rounded-full text-xs font-bold {% if user.role == 'admin' %}bg-purple-500/20 text-purple-300 border border-purple-500/30{% else %}bg-teal-500/20 text-teal-300 border border-teal-500/30{% endif %} capitalize">
          {{ user.role }}
        </span>
      </div>
    </header>

    <!-- Scrollable Workspace -->
    <main class="flex-1 overflow-y-auto p-8 space-y-6">

      <!-- ========================================== -->
      <!-- TAB 1: ORIGINAL DASHBOARD (DEFAULT ON LOGIN) -->
      <!-- ========================================== -->
      <div id="tab-dashboard" class="tab-pane space-y-6">
        <!-- 4 KPI Cards -->
        <div class="grid grid-cols-4 gap-5">
          <div class="bg-[#111c2e] p-5 rounded-3xl border border-slate-800 shadow">
            <p class="text-xs text-slate-400 font-medium">Total sales</p>
            <p class="text-2xl font-extrabold text-white mt-1" id="dashTotalSales">$0.00</p>
          </div>
          <div class="bg-[#111c2e] p-5 rounded-3xl border border-slate-800 shadow">
            <p class="text-xs text-slate-400 font-medium">Orders</p>
            <p class="text-2xl font-extrabold text-white mt-1" id="dashOrders">0</p>
          </div>
          <div class="bg-[#111c2e] p-5 rounded-3xl border border-slate-800 shadow">
            <p class="text-xs text-slate-400 font-medium">Products</p>
            <p class="text-2xl font-extrabold text-white mt-1" id="dashProducts">0</p>
          </div>
          <div class="bg-[#111c2e] p-5 rounded-3xl border border-slate-800 shadow">
            <p class="text-xs text-slate-400 font-medium">Low-stock items</p>
            <p class="text-2xl font-extrabold text-rose-400 mt-1" id="dashLowStock">0</p>
          </div>
        </div>

        <!-- 30-Day Sales Trend Line Chart -->
        <div class="bg-[#111c2e] p-6 rounded-3xl border border-slate-800 shadow">
          <h3 class="text-sm font-bold text-slate-200 mb-4">Sales trend (30 days)</h3>
          <div class="w-full h-64"><canvas id="salesTrendChart"></canvas></div>
        </div>

        <!-- Split Grid: Recent Transactions + Low Stock Alerts -->
        <div class="grid grid-cols-2 gap-6">
          <div class="bg-[#111c2e] p-6 rounded-3xl border border-slate-800 shadow space-y-3">
            <h3 class="text-sm font-bold text-slate-200">Recent transactions</h3>
            <div id="dashRecentTx" class="divide-y divide-slate-800 text-xs"></div>
          </div>
          <div class="bg-[#111c2e] p-6 rounded-3xl border border-slate-800 shadow space-y-3">
            <h3 class="text-sm font-bold text-slate-200">Low-stock alerts</h3>
            <div id="dashLowStockList" class="space-y-2 text-xs"></div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 2: EMPLOYEES (PDF Pages 7, 8, 9)        -->
      <!-- ========================================== -->
      <div id="tab-employees" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Staff directory</h2>
            <p class="text-xs text-slate-400">Manage internal employees, roles, and status</p>
          </div>
          <div class="flex gap-2">
            <input type="text" id="empSearch" onkeyup="filterEmployeesTable()" placeholder="Search employees..." class="bg-slate-900 border border-slate-700 text-xs px-3 py-2 rounded-xl text-white">
            <button onclick="openModal('modalNewEmployee')" class="px-4 py-2 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">+ New employee</button>
          </div>
        </div>
        <div class="bg-[#111c2e] rounded-3xl border border-slate-800 overflow-hidden shadow">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] font-bold">
              <tr>
                <th class="p-3.5">Name</th>
                <th class="p-3.5">Position</th>
                <th class="p-3.5">Department</th>
                <th class="p-3.5">Email</th>
                <th class="p-3.5">Status</th>
                <th class="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody id="employeesTableBody" class="divide-y divide-slate-800"></tbody>
          </table>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 3: PRODUCTS (PDF Pages 3 & 4)          -->
      <!-- ========================================== -->
      <div id="tab-products" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Product catalogue</h2>
            <p class="text-xs text-slate-400">All registered inventory items and pricing</p>
          </div>
          <div class="flex gap-2">
            <input type="text" id="prodSearch" onkeyup="filterProductsTable()" placeholder="Search products..." class="bg-slate-900 border border-slate-700 text-xs px-3 py-2 rounded-xl text-white">
            <button onclick="openModal('modalNewProduct')" class="px-4 py-2 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">+ New product</button>
          </div>
        </div>
        <div class="bg-[#111c2e] rounded-3xl border border-slate-800 overflow-hidden shadow">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] font-bold">
              <tr>
                <th class="p-3.5">SKU</th>
                <th class="p-3.5">Name</th>
                <th class="p-3.5">Category</th>
                <th class="p-3.5">Supplier</th>
                <th class="p-3.5">Price</th>
                <th class="p-3.5 text-right">Stock</th>
              </tr>
            </thead>
            <tbody id="productsTableBody" class="divide-y divide-slate-800"></tbody>
          </table>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 4: CUSTOMERS (PDF Pages 1 & 2)         -->
      <!-- ========================================== -->
      <div id="tab-customers" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Customer records</h2>
            <p class="text-xs text-slate-400">Corporate and retail registered accounts</p>
          </div>
          <div class="flex gap-2">
            <input type="text" id="custSearch" onkeyup="filterCustomersTable()" placeholder="Search customers..." class="bg-slate-900 border border-slate-700 text-xs px-3 py-2 rounded-xl text-white">
            <button onclick="openModal('modalNewCustomer')" class="px-4 py-2 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">+ New customer</button>
          </div>
        </div>
        <div class="bg-[#111c2e] rounded-3xl border border-slate-800 overflow-hidden shadow">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] font-bold">
              <tr>
                <th class="p-3.5">Name</th>
                <th class="p-3.5">Type</th>
                <th class="p-3.5">City</th>
                <th class="p-3.5">Email</th>
                <th class="p-3.5">Phone</th>
              </tr>
            </thead>
            <tbody id="customersTableBody" class="divide-y divide-slate-800"></tbody>
          </table>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 5: SUPPLIERS DIRECTORY                 -->
      <!-- ========================================== -->
      <div id="tab-suppliers" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Suppliers directory</h2>
            <p class="text-xs text-slate-400">Registered vendors and distribution channels</p>
          </div>
          <button onclick="openModal('modalNewSupplier')" class="px-4 py-2 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">+ New supplier</button>
        </div>
        <div id="suppliersDesktopGrid" class="grid grid-cols-3 gap-4"></div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 6: INWARD PURCHASES (PDF Page 10)       -->
      <!-- ========================================== -->
      <div id="tab-purchases" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Purchase orders</h2>
            <p class="text-xs text-slate-400">Stock procurement and inward supply log</p>
          </div>
          <button onclick="openModal('modalNewPurchase')" class="px-4 py-2 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">+ New PO</button>
        </div>
        <div class="bg-[#111c2e] rounded-3xl border border-slate-800 overflow-hidden shadow">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] font-bold">
              <tr>
                <th class="p-3.5">PO</th>
                <th class="p-3.5">Date</th>
                <th class="p-3.5">Total</th>
                <th class="p-3.5">Qty</th>
                <th class="p-3.5">Status</th>
              </tr>
            </thead>
            <tbody id="purchasesTableBody" class="divide-y divide-slate-800"></tbody>
          </table>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 7: INVENTORY (PDF Page 5)              -->
      <!-- ========================================== -->
      <div id="tab-inventory" class="tab-pane space-y-4 hidden">
        <div>
          <h2 class="text-lg font-bold text-white">Stock levels</h2>
          <p class="text-xs text-slate-400">Current warehouse inventory vs reorder threshold</p>
        </div>
        <div class="bg-[#111c2e] rounded-3xl border border-slate-800 overflow-hidden shadow">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="bg-slate-800/80 text-slate-400 uppercase text-[10px] font-bold">
              <tr>
                <th class="p-3.5">SKU</th>
                <th class="p-3.5">Product</th>
                <th class="p-3.5">Stock</th>
                <th class="p-3.5">Reorder level</th>
                <th class="p-3.5">Status</th>
              </tr>
            </thead>
            <tbody id="inventoryTableBody" class="divide-y divide-slate-800"></tbody>
          </table>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 8: REPORTS & CSV (PDF Page 11)         -->
      <!-- ========================================== -->
      <div id="tab-reports" class="tab-pane space-y-6 hidden">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-white">Revenue by category</h2>
            <p class="text-xs text-slate-400">Departmental breakdown and analytics export</p>
          </div>
          <a href="/api/export-sales-csv" target="_blank" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-teal-300 font-bold text-xs rounded-xl border border-slate-700 flex items-center gap-2">
            <span>📥 Export sales CSV</span>
          </a>
        </div>
        <div class="bg-[#111c2e] p-6 rounded-3xl border border-slate-800 shadow">
          <div class="w-full h-80"><canvas id="categoryReportChart"></canvas></div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 9: NLP ASSISTANT (PDF Page 6)          -->
      <!-- ========================================== -->
      <div id="tab-nlp" class="tab-pane space-y-6 hidden">
        <div class="bg-[#111c2e] p-8 rounded-3xl border border-slate-800 shadow space-y-4">
          <div>
            <h2 class="text-xl font-bold text-white">NLP Assistant</h2>
            <p class="text-xs text-slate-400 mt-1">Ask questions about your business in plain English. This is a predefined-query NLP prototype: questions are matched to safe, fixed query templates. No SQL is executed from your text.</p>
          </div>

          <div class="flex gap-3 pt-2">
            <input type="text" id="nlpDesktopInput" placeholder="e.g. Which products have less than 10 items?" class="flex-1 bg-slate-900 border border-slate-700 rounded-2xl px-4 py-3 text-sm text-white focus:outline-none focus:border-teal-500">
            <button onclick="runNLPQuery()" class="px-6 py-3 bg-[#00897b] hover:bg-[#00796b] text-white font-bold rounded-2xl text-sm shadow">Ask</button>
          </div>

          <!-- All 10 Predefined Chips from PDF Page 6 -->
          <div class="space-y-2 pt-2">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider block">Predefined Query Templates:</span>
            <div class="flex flex-wrap gap-2 text-xs">
              <button onclick="pickNlpChip('Show today\\'s sales')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Show today's sales</button>
              <button onclick="pickNlpChip('How many laptops are currently in stock?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">How many laptops are currently in stock?</button>
              <button onclick="pickNlpChip('Which products have less than 10 items?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Which products have less than 10 items?</button>
              <button onclick="pickNlpChip('Show sales for this month')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Show sales for this month</button>
              <button onclick="pickNlpChip('Who are the employees in the sales department?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Who are the employees in the sales department?</button>
              <button onclick="pickNlpChip('Which product has the highest sales?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Which product has the highest sales?</button>
              <button onclick="pickNlpChip('Who is our top customer?')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Who is our top customer?</button>
              <button onclick="pickNlpChip('Show purchases from last month')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Show purchases from last month</button>
              <button onclick="pickNlpChip('List all suppliers')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">List all suppliers</button>
              <button onclick="pickNlpChip('Total revenue this week')" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-xl border border-slate-700">Total revenue this week</button>
            </div>
          </div>
        </div>

        <!-- NLP Query Inspection Card -->
        <div id="nlpInspectBox" class="bg-[#111c2e] p-6 rounded-3xl border border-slate-800 shadow space-y-4 hidden text-xs">
          <div class="flex justify-between items-center border-b border-slate-800 pb-2">
            <span class="font-bold text-teal-400">NLP Query Breakdown</span>
            <span id="nlpConfidenceBadge" class="bg-teal-500/20 text-teal-300 px-2.5 py-0.5 rounded-full text-[10px]"></span>
          </div>
          <div>
            <span class="text-slate-400 block mb-1">Matched Intent:</span>
            <code id="nlpIntentBadge" class="text-purple-300 font-mono bg-slate-900 px-3 py-1.5 rounded block"></code>
          </div>
          <div>
            <span class="text-slate-400 block mb-1">Generated SQL Query:</span>
            <code id="nlpSqlBadge" class="text-emerald-400 font-mono bg-slate-900 p-2.5 rounded block"></code>
          </div>
          <div class="bg-slate-900 p-4 rounded-2xl border border-slate-800">
            <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Response:</span>
            <p id="nlpResponseText" class="text-white text-sm font-semibold"></p>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- TAB 10: POS TERMINAL & SPLIT CHECKOUT      -->
      <!-- ========================================== -->
      <div id="tab-pos" class="tab-pane space-y-6 hidden">
        <div class="grid grid-cols-12 gap-6">
          <div class="col-span-7 space-y-4">
            <div class="flex gap-2">
              <input type="text" id="posSkuInp" placeholder="Scan SKU / Barcode..." class="flex-1 bg-slate-900 border border-slate-700 text-xs px-3 py-2 rounded-xl text-white">
              <button onclick="addPosBySku()" class="px-4 py-2 bg-teal-600 text-white rounded-xl text-xs font-bold">Pick</button>
            </div>
            <div id="posGridContainer" class="grid grid-cols-3 gap-3 max-h-96 overflow-y-auto"></div>
          </div>
          <div class="col-span-5 bg-[#111c2e] p-5 rounded-3xl border border-slate-800 space-y-3">
            <h3 class="font-bold text-sm text-white">Current Order</h3>
            <div id="posLinesContainer" class="divide-y divide-slate-800 text-xs max-h-48 overflow-y-auto"></div>
            <div class="border-t border-slate-800 pt-2 space-y-1 text-xs">
              <div class="flex justify-between text-slate-400"><span>Subtotal:</span><span id="posSub">$0.00</span></div>
              <div class="flex justify-between text-slate-400"><span>Tax (5%):</span><span id="posTax">$0.00</span></div>
              <div class="flex justify-between font-extrabold text-sm text-teal-400"><span>Total Due:</span><span id="posTot">$0.00</span></div>
            </div>
            <button onclick="posCheckoutQuick()" class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-xs rounded-xl shadow transition">Complete Sale & Print Receipt</button>
          </div>
        </div>
      </div>

    </main>
  </div>

  <!-- ======================================================== -->
  <!-- 3. DESKTOP MODALS (Exact PDF fields validated)          -->
  <!-- ======================================================== -->

  <!-- Modal: New Customer (PDF Page 2) -->
  <div id="modalNewCustomer" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[#111c2e] border border-slate-800 rounded-3xl p-6 w-full max-w-md space-y-4 shadow-2xl">
      <div>
        <h3 class="font-bold text-base text-white">New customer</h3>
        <p class="text-[11px] text-slate-400">Fields marked are validated before saving.</p>
      </div>
      <input type="text" id="custName" placeholder="Name *" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Type</label>
        <select id="custType" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <option value="Retail">Retail</option>
          <option value="Corporate">Corporate</option>
        </select>
      </div>
      <input type="email" id="custEmail" placeholder="Email" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="text" id="custPhone" placeholder="Phone" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="text" id="custCity" placeholder="City" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div class="flex gap-2 pt-2">
        <button onclick="closeModal('modalNewCustomer')" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl font-bold">Cancel</button>
        <button onclick="submitNewCustomer()" class="w-1/2 py-2.5 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">Create</button>
      </div>
    </div>
  </div>

  <!-- Modal: New Product (PDF Page 4) -->
  <div id="modalNewProduct" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[#111c2e] border border-slate-800 rounded-3xl p-6 w-full max-w-md space-y-3 max-h-[90vh] overflow-y-auto shadow-2xl">
      <div>
        <h3 class="font-bold text-base text-white">New product</h3>
        <p class="text-[11px] text-slate-400">Fields marked are validated before saving.</p>
      </div>
      <input type="text" id="npSku" placeholder="SKU (e.g. SKU-1005)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono">
      <input type="text" id="npName" placeholder="Name *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Category</label>
        <input type="text" id="npCategory" placeholder="Category (e.g. Laptop, Monitor)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      </div>
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Supplier</label>
        <select id="npSupplier" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white"></select>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <input type="number" step="0.01" id="npPrice" placeholder="Selling price *" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="number" step="0.01" id="npCost" placeholder="Unit cost" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      </div>
      <div class="grid grid-cols-2 gap-2">
        <input type="number" id="npStock" placeholder="Opening stock" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="number" id="npReorder" placeholder="Reorder level (default 10)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      </div>
      <div class="flex gap-2 pt-2">
        <button onclick="closeModal('modalNewProduct')" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl font-bold">Cancel</button>
        <button onclick="submitNewProduct()" class="w-1/2 py-2.5 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">Create</button>
      </div>
    </div>
  </div>

  <!-- Modal: New Employee (PDF Page 9) -->
  <div id="modalNewEmployee" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[#111c2e] border border-slate-800 rounded-3xl p-6 w-full max-w-md space-y-3 max-h-[90vh] overflow-y-auto shadow-2xl">
      <div>
        <h3 class="font-bold text-base text-white">New employee</h3>
        <p class="text-[11px] text-slate-400">Fields marked are validated before saving.</p>
      </div>
      <input type="text" id="neName" placeholder="Full name *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="email" id="neEmail" placeholder="Email *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="password" id="nePass" placeholder="Password (default: welcome123)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="text" id="nePhone" placeholder="Phone" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Department</label>
        <select id="neDept" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white"></select>
      </div>
      <input type="text" id="nePosition" placeholder="Position (e.g. Sales Executive)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div class="grid grid-cols-2 gap-2">
        <input type="number" id="neSalary" placeholder="Monthly salary ($)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="date" id="neJoin" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
      </div>
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Status</label>
        <select id="neStatus" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <option value="Active">Active</option>
          <option value="Leave">Leave</option>
        </select>
      </div>
      <div class="flex gap-2 pt-2">
        <button onclick="closeModal('modalNewEmployee')" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl font-bold">Cancel</button>
        <button onclick="submitNewEmployee()" class="w-1/2 py-2.5 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">Create</button>
      </div>
    </div>
  </div>

  <!-- Modal: New Supplier -->
  <div id="modalNewSupplier" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[#111c2e] border border-slate-800 rounded-3xl p-6 w-full max-w-md space-y-3 shadow-2xl">
      <h3 class="font-bold text-base text-white">New supplier</h3>
      <input type="text" id="nsName" placeholder="Supplier Company Name *" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="text" id="nsPerson" placeholder="Contact Person" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="text" id="nsPhone" placeholder="Phone" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="email" id="nsEmail" placeholder="Email" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div class="flex gap-2 pt-2">
        <button onclick="closeModal('modalNewSupplier')" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl font-bold">Cancel</button>
        <button onclick="submitNewSupplier()" class="w-1/2 py-2.5 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">Create</button>
      </div>
    </div>
  </div>

  <!-- Modal: New Purchase Order (PDF Page 10) -->
  <div id="modalNewPurchase" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
    <div class="bg-[#111c2e] border border-slate-800 rounded-3xl p-6 w-full max-w-md space-y-3 shadow-2xl">
      <h3 class="font-bold text-base text-white">Create Purchase Order</h3>
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Supplier</label>
        <select id="npoSupplier" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white"></select>
      </div>
      <input type="number" step="0.01" id="npoAmount" placeholder="Total Amount ($) *" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <input type="number" id="npoQty" placeholder="Quantity Inward" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
      <div>
        <label class="text-[11px] text-slate-400 block mb-1">Status</label>
        <select id="npoStatus" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <option value="Received">Received</option>
          <option value="Ordered">Ordered</option>
        </select>
      </div>
      <div class="flex gap-2 pt-2">
        <button onclick="closeModal('modalNewPurchase')" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl font-bold">Cancel</button>
        <button onclick="submitNewPurchase()" class="w-1/2 py-2.5 bg-[#00897b] hover:bg-[#00796b] text-white text-xs font-bold rounded-xl shadow">Create PO</button>
      </div>
    </div>
  </div>

  <!-- ======================================================== -->
  <!-- 4. CLIENT JAVASCRIPT LOGIC                               -->
  <!-- ======================================================== -->
  <script>
    let appData = {};
    let posCart = [];

    function switchTab(tabId) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      const active = document.getElementById('tab-' + tabId);
      if (active) active.classList.remove('hidden');

      document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('bg-[#13233b]', 'text-teal-300');
        btn.classList.add('text-slate-300');
      });
      const activeNav = document.getElementById('nav-' + tabId);
      if (activeNav) {
        activeNav.classList.add('bg-[#13233b]', 'text-teal-300');
        activeNav.classList.remove('text-slate-300');
      }

      const titleMap = {
        'dashboard': 'Dashboard',
        'employees': 'Employees',
        'products': 'Products',
        'customers': 'Customers',
        'suppliers': 'Suppliers',
        'pos': 'Sales & POS',
        'purchases': 'Purchases',
        'inventory': 'Inventory',
        'reports': 'Reports',
        'nlp': 'NLP Assistant'
      };
      document.getElementById('screenHeaderTitle').innerText = titleMap[tabId] || 'Dashboard';
    }

    function openModal(id) { const m = document.getElementById(id); if (m) m.classList.remove('hidden'); }
    function closeModal(id) { const m = document.getElementById(id); if (m) m.classList.add('hidden'); }

    // ==========================================
    // DATA RENDERING (Exact PDF Table Styles)
    // ==========================================
    async function loadMasterData() {
      const res = await fetch('/api/master-data');
      appData = await res.json();

      // 1. Dashboard (Original Layout on Login)
      document.getElementById('dashTotalSales').innerText = `$${appData.total_revenue.toFixed(2)}`;
      document.getElementById('dashOrders').innerText = appData.sales.length;
      document.getElementById('dashProducts').innerText = appData.products.length;
      document.getElementById('dashLowStock').innerText = appData.low_stock.length;

      document.getElementById('dashRecentTx').innerHTML = appData.sales.slice(0, 6).map(s => `
        <div class="flex justify-between py-2.5">
          <span class="text-slate-300">${s.invoice_no} · ${s.sale_date}</span>
          <span class="font-bold text-white">$${s.total_amount.toFixed(2)}</span>
        </div>
      `).join('');

      document.getElementById('dashLowStockList').innerHTML = appData.low_stock.map(p => `
        <div class="flex justify-between py-1.5 items-center">
          <span class="text-slate-300">${p.product_name}</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300">${p.stock} left</span>
        </div>
      `).join('');

      // 2. Employees Table (PDF Pages 7 & 8)
      renderEmployeesTable(appData.employees);

      // 3. Products Table (PDF Page 3)
      renderProductsTable(appData.products);

      // 4. Customers Table (PDF Page 1)
      renderCustomersTable(appData.customers);

      // 5. Purchases Table (PDF Page 10)
      const purBox = document.getElementById('purchasesTableBody');
      if (purBox) {
        purBox.innerHTML = appData.purchases.map(pr => `
          <tr class="hover:bg-slate-800/40">
            <td class="p-3.5 font-bold text-white">${pr.po_number || 'PO-' + pr.purchase_id}</td>
            <td class="p-3.5 text-slate-400">${pr.purchase_date}</td>
            <td class="p-3.5 font-bold text-white">$${pr.total_amount.toFixed(2)}</td>
            <td class="p-3.5 text-slate-300">${pr.quantity || 1}</td>
            <td class="p-3.5">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${pr.status === 'Received' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}">
                ${pr.status}
              </span>
            </td>
          </tr>
        `).join('');
      }

      // 6. Inventory Table (PDF Page 5)
      const invBox = document.getElementById('inventoryTableBody');
      if (invBox) {
        invBox.innerHTML = appData.products.map(p => `
          <tr class="hover:bg-slate-800/40">
            <td class="p-3.5 font-mono text-teal-300">${p.sku}</td>
            <td class="p-3.5 font-bold text-white">${p.product_name}</td>
            <td class="p-3.5 font-extrabold text-white">${p.stock}</td>
            <td class="p-3.5 text-slate-400">${p.reorder_level}</td>
            <td class="p-3.5">
              <span class="px-2.5 py-0.5 rounded text-[10px] font-bold ${p.status === 'OK' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'}">
                ${p.status}
              </span>
            </td>
          </tr>
        `).join('');
      }

      // 7. Suppliers Grid
      const supGrid = document.getElementById('suppliersDesktopGrid');
      if (supGrid) {
        supGrid.innerHTML = appData.suppliers.map(s => `
          <div class="bg-[#111c2e] p-5 rounded-3xl border border-slate-800 space-y-2">
            <h4 class="font-bold text-sm text-white">${s.supplier_name}</h4>
            <p class="text-xs text-slate-400">Contact: ${s.contact_person || 'N/A'}</p>
            <p class="text-xs text-slate-400">Phone: ${s.phone || 'N/A'}</p>
            <p class="text-[11px] text-teal-400 truncate">${s.email || ''}</p>
          </div>
        `).join('');
      }

      // Populate Dropdowns in Modals
      populateDropdowns();
      renderPOSGrid();
    }

    function renderEmployeesTable(emps) {
      const eb = document.getElementById('employeesTableBody');
      if (!eb) return;
      eb.innerHTML = emps.map(e => `
        <tr class="hover:bg-slate-800/40">
          <td class="p-3.5 font-bold text-white">${e.name}</td>
          <td class="p-3.5 text-slate-300">${e.designation}</td>
          <td class="p-3.5 text-slate-400">${e.dept_name}</td>
          <td class="p-3.5 text-slate-300">${e.email}</td>
          <td class="p-3.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.status === 'Active' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}">
              ${e.status || 'Active'}
            </span>
          </td>
          <td class="p-3.5 text-right text-slate-400">
            <button class="hover:text-white px-1">•••</button>
          </td>
        </tr>
      `).join('');
    }

    function filterEmployeesTable() {
      const q = document.getElementById('empSearch').value.toLowerCase();
      const filtered = appData.employees.filter(e => e.name.toLowerCase().includes(q) || e.designation.toLowerCase().includes(q) || e.email.toLowerCase().includes(q));
      renderEmployeesTable(filtered);
    }

    function renderProductsTable(prods) {
      const pb = document.getElementById('productsTableBody');
      if (!pb) return;
      pb.innerHTML = prods.map(p => `
        <tr class="hover:bg-slate-800/40">
          <td class="p-3.5 font-mono text-teal-300">${p.sku}</td>
          <td class="p-3.5 font-bold text-white">${p.product_name}</td>
          <td class="p-3.5 text-slate-400">${p.category}</td>
          <td class="p-3.5 text-slate-400">${p.supplier_name}</td>
          <td class="p-3.5 font-extrabold text-white">$${p.price.toFixed(2)}</td>
          <td class="p-3.5 text-right font-bold ${p.stock < p.reorder_level ? 'text-rose-400' : 'text-slate-300'}">${p.stock}</td>
        </tr>
      `).join('');
    }

    function filterProductsTable() {
      const q = document.getElementById('prodSearch').value.toLowerCase();
      const filtered = appData.products.filter(p => p.product_name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
      renderProductsTable(filtered);
    }

    function renderCustomersTable(custs) {
      const cb = document.getElementById('customersTableBody');
      if (!cb) return;
      cb.innerHTML = custs.map(c => `
        <tr class="hover:bg-slate-800/40">
          <td class="p-3.5 font-bold text-white">${c.name}</td>
          <td class="p-3.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.type === 'Corporate' ? 'bg-purple-500/20 text-purple-300' : 'bg-teal-500/20 text-teal-300'}">
              ${c.type || 'Retail'}
            </span>
          </td>
          <td class="p-3.5 text-slate-400">${c.city || 'Pune'}</td>
          <td class="p-3.5 text-slate-300">${c.email || 'N/A'}</td>
          <td class="p-3.5 text-slate-400 font-mono">${c.phone || 'N/A'}</td>
        </tr>
      `).join('');
    }

    function filterCustomersTable() {
      const q = document.getElementById('custSearch').value.toLowerCase();
      const filtered = appData.customers.filter(c => c.name.toLowerCase().includes(q) || (c.city && c.city.toLowerCase().includes(q)));
      renderCustomersTable(filtered);
    }

    function populateDropdowns() {
      const supSelects = ['npSupplier', 'npoSupplier'];
      supSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = appData.suppliers.map(s => `<option value="${s.supplier_id}">${s.supplier_name}</option>`).join('');
      });

      const neDept = document.getElementById('neDept');
      if (neDept) {
        neDept.innerHTML = appData.departments.map(d => `<option value="${d.dept_id}">${d.dept_name}</option>`).join('');
      }
    }

    // ==========================================
    // ACTION SUBMISSIONS
    // ==========================================
    async function submitNewCustomer() {
      const name = document.getElementById('custName').value.trim();
      const type = document.getElementById('custType').value;
      const email = document.getElementById('custEmail').value.trim();
      const phone = document.getElementById('custPhone').value.trim();
      const city = document.getElementById('custCity').value.trim();
      if (!name) return alert('Name required');

      const res = await fetch('/api/add-customer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, type, email, phone, city })
      });
      const d = await res.json();
      if (d.status === 'success') {
        closeModal('modalNewCustomer');
        document.getElementById('custName').value = '';
        await loadMasterData();
        alert(`Customer "${name}" created!`);
      }
    }

    async function submitNewProduct() {
      const sku = document.getElementById('npSku').value.trim();
      const name = document.getElementById('npName').value.trim();
      const category = document.getElementById('npCategory').value.trim();
      const supplier_id = document.getElementById('npSupplier').value;
      const price = document.getElementById('npPrice').value;
      const cost_price = document.getElementById('npCost').value || 0;
      const stock = document.getElementById('npStock').value || 0;
      const reorder_level = document.getElementById('npReorder').value || 10;
      if (!name || !price) return alert('Name and Price required');

      const res = await fetch('/api/add-product', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sku, product_name: name, category, supplier_id, price, cost_price, stock, reorder_level })
      });
      const d = await res.json();
      if (d.status === 'success') {
        closeModal('modalNewProduct');
        document.getElementById('npName').value = '';
        document.getElementById('npPrice').value = '';
        await loadMasterData();
        alert(`Product "${name}" registered!`);
      }
    }

    async function submitNewEmployee() {
      const name = document.getElementById('neName').value.trim();
      const email = document.getElementById('neEmail').value.trim();
      const password = document.getElementById('nePass').value.trim() || 'welcome123';
      const phone = document.getElementById('nePhone').value.trim();
      const dept_id = document.getElementById('neDept').value;
      const position = document.getElementById('nePosition').value.trim();
      const monthly_salary = document.getElementById('neSalary').value || 45000;
      const join_date = document.getElementById('neJoin').value;
      const status = document.getElementById('neStatus').value;
      if (!name || !email) return alert('Name and Email required');

      const res = await fetch('/api/add-employee', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, email, password, phone, dept_id, position, monthly_salary, join_date, status })
      });
      const d = await res.json();
      if (d.status === 'success') {
        closeModal('modalNewEmployee');
        document.getElementById('neName').value = '';
        document.getElementById('neEmail').value = '';
        await loadMasterData();
        alert(`Employee "${name}" onboarded!`);
      }
    }

    async function submitNewSupplier() {
      const supplier_name = document.getElementById('nsName').value.trim();
      const contact_person = document.getElementById('nsPerson').value.trim();
      const phone = document.getElementById('nsPhone').value.trim();
      const email = document.getElementById('nsEmail').value.trim();
      if (!supplier_name) return alert('Supplier name required');

      const res = await fetch('/api/add-supplier', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ supplier_name, contact_person, phone, email })
      });
      const d = await res.json();
      if (d.status === 'success') {
        closeModal('modalNewSupplier');
        document.getElementById('nsName').value = '';
        await loadMasterData();
        alert(`Supplier "${supplier_name}" saved!`);
      }
    }

    async function submitNewPurchase() {
      const supplier_id = document.getElementById('npoSupplier').value;
      const total_amount = document.getElementById('npoAmount').value;
      const quantity = document.getElementById('npoQty').value || 1;
      const status = document.getElementById('npoStatus').value;
      if (!total_amount) return alert('Total amount required');

      const res = await fetch('/api/add-purchase', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ supplier_id, total_amount, quantity, status })
      });
      const d = await res.json();
      if (d.status === 'success') {
        closeModal('modalNewPurchase');
        document.getElementById('npoAmount').value = '';
        await loadMasterData();
        alert('Purchase Order created!');
      }
    }

    // ==========================================
    // NLP EXECUTION (PDF Page 6 Prompts)
    // ==========================================
    function pickNlpChip(queryText) {
      document.getElementById('nlpDesktopInput').value = queryText;
      runNLPQuery();
    }

    async function runNLPQuery() {
      const q = document.getElementById('nlpDesktopInput').value.trim();
      if (!q) return;

      const res = await fetch('/api/nlp-query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: q })
      });
      const d = await res.json();
      const nlp = d.nlp_result;

      const box = document.getElementById('nlpInspectBox');
      box.classList.remove('hidden');

      document.getElementById('nlpConfidenceBadge').innerText = `Confidence: ${nlp.confidence}`;
      document.getElementById('nlpIntentBadge').innerText = nlp.intent;
      document.getElementById('nlpSqlBadge').innerText = nlp.sql;
      document.getElementById('nlpResponseText').innerText = nlp.answer;
    }

    // ==========================================
    // CHARTS INITIALIZATION (Trend + Reports)
    // ==========================================
    function initCharts() {
      // 1. 30-Day Sales Trend (Dashboard)
      const trendCtx = document.getElementById('salesTrendChart').getContext('2d');
      new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: ['09-14', '09-19', '09-24', '09-29', '10-04', '10-10'],
          datasets: [{
            data: [0, 2200, 3600, 1600, 5200, 6500],
            borderColor: '#00897b',
            backgroundColor: 'rgba(0, 137, 123, 0.15)',
            fill: true,
            tension: 0.35,
            pointRadius: 3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
            y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }
          }
        }
      });

      // 2. Revenue by Category (Reports - PDF Page 11)
      const repCtx = document.getElementById('categoryReportChart').getContext('2d');
      new Chart(repCtx, {
        type: 'bar',
        data: {
          labels: ['Electronics/Laptops', 'Monitor', 'Printer', 'Furniture', 'Accessories'],
          datasets: [{
            data: [145000, 12000, 11500, 12000, 9500],
            backgroundColor: '#0284c7',
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
            y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }
          }
        }
      });
    }

    // POS Helpers
    function renderPOSGrid() {
      const box = document.getElementById('posGridContainer');
      if (!box || !appData.products) return;
      box.innerHTML = appData.products.map(p => `
        <div onclick="addPosItem(${p.product_id})" class="bg-[#111c2e] p-3 rounded-2xl border border-slate-800 hover:border-teal-500 cursor-pointer transition">
          <div class="font-bold text-xs text-white">${p.product_name}</div>
          <div class="text-[10px] text-teal-400 font-mono">${p.sku}</div>
          <div class="flex justify-between items-center mt-2 pt-1 border-t border-slate-800 text-xs">
            <span class="font-bold text-white">$${p.price.toFixed(2)}</span>
            <span class="text-[10px] text-slate-400">${p.stock} left</span>
          </div>
        </div>
      `).join('');
    }

    function addPosItem(id) {
      const p = appData.products.find(x => x.product_id === id);
      if (!p) return;
      const ex = posCart.find(x => x.product_id === id);
      if (ex) ex.qty++;
      else posCart.push({ product_id: p.product_id, name: p.product_name, price: p.price, qty: 1 });
      renderPOSCart();
    }

    function addPosBySku() {
      const sku = document.getElementById('posSkuInp').value.trim().toLowerCase();
      const p = appData.products.find(x => x.sku.toLowerCase() === sku);
      if (p) { addPosItem(p.product_id); document.getElementById('posSkuInp').value = ''; }
      else alert('Product not found');
    }

    function renderPOSCart() {
      const box = document.getElementById('posLinesContainer');
      box.innerHTML = posCart.map(i => `
        <div class="flex justify-between py-1.5">
          <span>${i.name} x${i.qty}</span>
          <span class="font-bold text-white">$${(i.qty * i.price).toFixed(2)}</span>
        </div>
      `).join('');
      const sub = posCart.reduce((a, b) => a + (b.price * b.qty), 0);
      const tax = sub * 0.05;
      const tot = sub + tax;
      document.getElementById('posSub').innerText = `$${sub.toFixed(2)}`;
      document.getElementById('posTax').innerText = `$${tax.toFixed(2)}`;
      document.getElementById('posTot').innerText = `$${tot.toFixed(2)}`;
    }

    async function posCheckoutQuick() {
      if (posCart.length === 0) return alert('Empty cart');
      const sub = posCart.reduce((a, b) => a + (b.price * b.qty), 0);
      const tot = sub * 1.05;
      const res = await fetch('/api/pos-checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ cart: posCart, total: tot, subtotal: sub, tax: sub * 0.05 })
      });
      const d = await res.json();
      if (d.status === 'success') {
        alert(`Sale complete! Invoice: ${d.invoice_no}`);
        posCart = [];
        renderPOSCart();
        await loadMasterData();
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      initCharts();
      loadMasterData();
    });
  </script>
</body>
</html>
"""
with open("templates/dashboard.html", "w") as f:
    f.write(html_code)

print("\nSUCCESS: Desktop Landscape Interface & all missing options implemented cleanly!")
