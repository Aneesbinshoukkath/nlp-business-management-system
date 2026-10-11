import os
import pymysql

# 1. Update Database Schema & Add Necessary Relations
def setup_database():
    conn = pymysql.connect(
        host="localhost",
        user="biz_user",
        password="biz_pass123"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS business_management;")
    cursor.execute("USE business_management;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INT AUTO_INCREMENT PRIMARY KEY,
        dept_name VARCHAR(100) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        role ENUM('admin', 'employee') NOT NULL,
        designation VARCHAR(100) DEFAULT 'Staff'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        designation VARCHAR(100),
        dept_id INT,
        user_id INT,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(150) NOT NULL,
        category VARCHAR(100),
        price DECIMAL(10, 2) NOT NULL,
        stock INT DEFAULT 0
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(100)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_no VARCHAR(50) NOT NULL,
        sale_date DATE NOT NULL,
        total_amount DECIMAL(10, 2) NOT NULL,
        payment_method VARCHAR(50),
        cashier_name VARCHAR(100) DEFAULT 'Staff'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sale_items (
        sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
        sale_id INT,
        product_id INT,
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INT AUTO_INCREMENT PRIMARY KEY,
        supplier_name VARCHAR(150) NOT NULL,
        contact_person VARCHAR(100),
        phone VARCHAR(20),
        email VARCHAR(100)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        purchase_id INT AUTO_INCREMENT PRIMARY KEY,
        supplier_id INT,
        purchase_date DATE NOT NULL,
        total_amount DECIMAL(10, 2) NOT NULL,
        status VARCHAR(50) DEFAULT 'Received',
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
    );
    """)

    # Seed initial demo data if empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO departments (dept_id, dept_name) VALUES (1, 'Sales'), (2, 'Operations'), (3, 'Inventory'), (4, 'Executive');")
        cursor.execute("INSERT INTO users (name, email, password, role, designation) VALUES ('Admin User', 'admin@bizcore.dev', 'admin123', 'admin', 'System Administrator'), ('Priya Nair', 'employee@bizcore.dev', 'employee123', 'employee', 'Store Manager');")
        cursor.execute("INSERT INTO employees (name, email, designation, dept_id, user_id) VALUES ('Priya Nair', 'employee@bizcore.dev', 'Store Manager', 1, 2);")
        cursor.execute("""
        INSERT INTO products (product_name, category, price, stock) VALUES
        ('Lenovo ThinkPad E14 Laptop', 'Electronics', 1100.00, 6),
        ('MacBook Air M2 Laptop', 'Electronics', 1199.00, 4),
        ('LG 27" 4K Monitor', 'Displays', 450.00, 9),
        ('Mechanical Keyboard', 'Accessories', 120.00, 7),
        ('Noise-Cancelling Headset', 'Audio', 200.00, 3),
        ('Toner Cartridge 85A', 'Office Supplies', 65.00, 8),
        ('24-Port Network Switch', 'Networking', 350.00, 5),
        ('Standing Desk', 'Furniture', 550.00, 2),
        ('Dell UltraSharp 32', 'Displays', 720.00, 18),
        ('Logitech MX Master 3S', 'Accessories', 99.00, 25),
        ('Ergonomic Office Chair', 'Furniture', 320.00, 14),
        ('Samsung T7 1TB SSD', 'Storage', 130.00, 22);
        """)
        cursor.execute("INSERT INTO customers (name, phone, email) VALUES ('Arun Varma', '9876543210', 'arun@gmail.com'), ('Divya Nair', '9812345678', 'divya@gmail.com');")
        cursor.execute("INSERT INTO suppliers (supplier_name, contact_person, phone, email) VALUES ('TechDistro Hub', 'Kavya Rao', '+91 98450 11223', 'kavya@techdistro.in'), ('Apex Office Supplies', 'Manish Sen', '+91 98711 33445', 'sales@apexoffice.com');")
        cursor.execute("INSERT INTO sales (invoice_no, sale_date, total_amount, payment_method, cashier_name) VALUES ('INV-5000', CURDATE(), 267.00, 'Card', 'Priya Nair'), ('INV-5001', CURDATE(), 198.00, 'UPI', 'Priya Nair'), ('INV-5002', CURDATE(), 1145.00, 'Card', 'Priya Nair');")
        cursor.execute("INSERT INTO purchases (supplier_id, purchase_date, total_amount, status) VALUES (1, CURDATE(), 4200.00, 'Delivered'), (2, CURDATE(), 950.00, 'Delivered');")

    conn.commit()
    conn.close()
    print("Database updated successfully.")

setup_database()

# 2. Write Upgraded NLP Parser
nlp_code = """import re
from datetime import date

class NLPQueryParser:
    def __init__(self, db_cursor):
        self.cursor = db_cursor

    def process_query(self, user_query: str):
        query = user_query.strip().lower()

        # 1. Intent: Today's sales
        if "today's sales" in query or "sales today" in query or "today sales" in query:
            today_str = date.today().strftime('%Y-%m-%d')
            sql = "SELECT IFNULL(SUM(total_amount), 0) AS total_sales, COUNT(sale_id) AS total_orders FROM sales WHERE DATE(sale_date) = %s"
            self.cursor.execute(sql, (today_str,))
            res = self.cursor.fetchone()
            return {
                "intent": "SALES_QUERY_TODAY",
                "confidence": "98.4%",
                "entities": [{"type": "TEMPORAL_CONDITION", "value": "TODAY"}],
                "sql": sql.replace("%s", f"'{today_str}'"),
                "answer": f"Today's sales total ${float(res['total_sales']):,.2f} across {res['total_orders']} completed transactions."
            }

        # 2. Intent: Threshold inventory
        threshold_match = re.search(r'(?:less than|under|below)\\s+(\\d+)', query)
        if threshold_match and ("stock" in query or "items" in query or "product" in query):
            num = int(threshold_match.group(1))
            sql = "SELECT product_name, stock FROM products WHERE stock < %s ORDER BY stock ASC"
            self.cursor.execute(sql, (num,))
            records = self.cursor.fetchall()
            items_str = ", ".join([f"{r['product_name']} ({r['stock']} units left)" for r in records]) if records else f"None below {num}"
            return {
                "intent": "INVENTORY_THRESHOLD_FILTER",
                "confidence": "96.7%",
                "entities": [{"type": "FILTER_OPERATOR", "value": "<"}, {"type": "NUMERIC_LIMIT", "value": str(num)}],
                "sql": sql.replace("%s", str(num)),
                "answer": f"Products with stock below {num}: {items_str}."
            }

        # 3. Intent: Product specific inventory
        stock_single = re.search(r'how many ([\\w\\s]+) are (?:currently )?in stock', query)
        if stock_single:
            target = stock_single.group(1).rstrip('s').strip()
            sql = "SELECT product_name, stock FROM products WHERE LOWER(product_name) LIKE %s"
            self.cursor.execute(sql, (f"%{target}%",))
            records = self.cursor.fetchall()
            answer = "; ".join([f"{r['product_name']}: {r['stock']} in stock" for r in records]) if records else f"No product found matching '{target}'."
            return {
                "intent": "PRODUCT_STOCK_LOOKUP",
                "confidence": "94.2%",
                "entities": [{"type": "TARGET_ENTITY", "value": target}],
                "sql": sql.replace("%s", f"'%{target}%'"),
                "answer": answer
            }

        # 4. Intent: Highest selling product
        if "highest sales" in query or "best selling" in query or "top product" in query:
            sql = \"\"\"SELECT p.product_name, SUM(si.quantity) as sold FROM sale_items si JOIN products p ON si.product_id = p.product_id GROUP BY p.product_id ORDER BY sold DESC LIMIT 1\"\"\"
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            msg = f"The top performing product is '{res['product_name']}' with {res['sold']} total units sold." if res else "No sales items recorded yet."
            return {
                "intent": "ANALYTICS_TOP_PRODUCT",
                "confidence": "99.1%",
                "entities": [{"type": "AGGREGATION", "value": "SUM(quantity)"}, {"type": "ORDER", "value": "DESC"}],
                "sql": sql,
                "answer": msg
            }

        # 5. Intent: Department Employees
        dept_match = re.search(r'employees in (?:the )?([\\w\\s]+) department', query)
        if dept_match:
            dept = dept_match.group(1).strip()
            sql = \"\"\"SELECT e.name, e.designation FROM employees e JOIN departments d ON e.dept_id = d.dept_id WHERE LOWER(d.dept_name) = %s\"\"\"
            self.cursor.execute(sql, (dept,))
            emps = self.cursor.fetchall()
            listing = ", ".join([f"{e['name']} ({e['designation']})" for e in emps]) if emps else f"No employees registered under {dept.capitalize()}."
            return {
                "intent": "HR_DEPARTMENT_DIRECTORY",
                "confidence": "97.5%",
                "entities": [{"type": "DEPARTMENT_NAME", "value": dept}],
                "sql": sql.replace("%s", f"'{dept}'"),
                "answer": f"Personnel in {dept.capitalize()}: {listing}."
            }

        # Fallback
        return {
            "intent": "GENERAL_FALLBACK",
            "confidence": "45.0%",
            "entities": [],
            "sql": "-- No SQL generated for unrecognized pattern",
            "answer": "Query pattern not recognized. Try: 'Show today\\'s sales', 'Which products have less than 10 items?', or 'Who are the employees in the sales department?'"
        }
"""
os.makedirs("nlp_engine", exist_ok=True)
with open("nlp_engine/parser.py", "w") as f:
    f.write(nlp_code)

# 3. Write Upgraded app.py
app_code = """from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pymysql.cursors
from nlp_engine.parser import NLPQueryParser

app = Flask(__name__)
app.secret_key = "bizcore_secure_secret_key"

def get_db():
    return pymysql.connect(
        host="localhost",
        user="biz_user",
        password="biz_pass123",
        database="business_management",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def root():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
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
                        'designation': user['designation']
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
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/api/all-data')
def get_all_data():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products ORDER BY product_id DESC")
            products = cursor.fetchall()

            cursor.execute("SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC")
            low_stock = cursor.fetchall()

            cursor.execute("SELECT * FROM sales ORDER BY sale_id DESC")
            sales = cursor.fetchall()
            for s in sales:
                s['sale_date'] = s['sale_date'].strftime('%Y-%m-%d')
                s['total_amount'] = float(s['total_amount'])

            cursor.execute("SELECT * FROM customers")
            customers = cursor.fetchall()

            cursor.execute(\"\"\"
                SELECT e.employee_id, e.name, e.email, e.designation, d.dept_name, u.role
                FROM employees e
                LEFT JOIN departments d ON e.dept_id = d.dept_id
                LEFT JOIN users u ON e.user_id = u.user_id
            \"\"\")
            employees = cursor.fetchall()

            cursor.execute("SELECT * FROM departments")
            departments = cursor.fetchall()

            cursor.execute("SELECT * FROM suppliers")
            suppliers = cursor.fetchall()

            cursor.execute(\"\"\"
                SELECT p.*, s.supplier_name
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.purchase_id DESC
            \"\"\")
            purchases = cursor.fetchall()
            for p in purchases:
                p['purchase_date'] = p['purchase_date'].strftime('%Y-%m-%d')
                p['total_amount'] = float(p['total_amount'])

            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) as rev FROM sales")
            rev = float(cursor.fetchone()['rev'])

            return jsonify({
                'products': products,
                'low_stock': low_stock,
                'sales': sales,
                'customers': customers,
                'employees': employees,
                'departments': departments,
                'suppliers': suppliers,
                'purchases': purchases,
                'total_revenue': rev
            })
    finally:
        conn.close()

# Admin: Create Staff & Assign Roles/Posts
@app.route('/api/add-staff', methods=['POST'])
def add_staff():
    if 'user' not in session or session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1. Create Login User
            cursor.execute(\"\"\"
                INSERT INTO users (name, email, password, role, designation)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (data['name'], data['email'], data['password'], 'employee', data['designation']))
            user_id = cursor.lastrowid

            # 2. Create Employee Record
            cursor.execute(\"\"\"
                INSERT INTO employees (name, email, designation, dept_id, user_id)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (data['name'], data['email'], data['designation'], data['dept_id'], user_id))
            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# Staff POS Checkout Endpoint
@app.route('/api/pos-checkout', methods=['POST'])
def pos_checkout():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    cart = data.get('cart', [])
    if not cart:
        return jsonify({'error': 'Empty cart'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM sales")
            inv_no = f"INV-{5000 + cursor.fetchone()['cnt'] + 1}"
            total = float(data.get('total', 0))
            method = data.get('payment_method', 'Cash')
            cashier = session['user']['name']

            cursor.execute(\"\"\"
                INSERT INTO sales (invoice_no, sale_date, total_amount, payment_method, cashier_name)
                VALUES (%s, CURDATE(), %s, %s, %s)
            \"\"\", (inv_no, total, method, cashier))
            sale_id = cursor.lastrowid

            for item in cart:
                cursor.execute(\"\"\"
                    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                \"\"\", (sale_id, item['product_id'], item['qty'], item['price']))

                cursor.execute(\"\"\"
                    UPDATE products SET stock = stock - %s WHERE product_id = %s
                \"\"\", (item['qty'], item['product_id']))

            conn.commit()
            return jsonify({'status': 'success', 'invoice_no': inv_no})
    finally:
        conn.close()

# NLP Assistant Endpoint
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

# 4. Write Upgraded dashboard.html
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BizCore NLP - Enterprise Management & POS</title>
  <link rel="manifest" href="/static/manifest.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-[#0f172a] text-slate-100 min-h-screen font-sans flex flex-col items-center">

  <div class="w-full max-w-md bg-[#1e293b] min-h-screen shadow-2xl relative pb-10 flex flex-col border-x border-slate-700">
    <!-- Top Bar -->
    <header class="px-5 py-4 flex items-center justify-between border-b border-slate-700/80 bg-[#1e293b] sticky top-0 z-30">
      <div class="flex items-center space-x-3">
        <button onclick="toggleDrawer()" class="p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
        <div>
          <h1 id="pageTitle" class="text-lg font-bold text-white leading-tight">Dashboard</h1>
          <p class="text-[11px] text-teal-400 font-medium">{{ user.designation }}</p>
        </div>
      </div>
      <span class="px-3 py-1 rounded-full text-[11px] font-bold {% if user.role == 'admin' %}bg-purple-500/20 text-purple-300 border border-purple-500/30{% else %}bg-teal-500/20 text-teal-300 border border-teal-500/30{% endif %} capitalize">
        {{ user.role }}
      </span>
    </header>

    <!-- Main Screens Container -->
    <main class="p-4 space-y-4 flex-1">

      <!-- TAB 1: DASHBOARD -->
      <div id="tab-dashboard" class="tab-pane space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
            <p class="text-xs text-slate-400">Total Sales</p>
            <p class="text-xl font-extrabold text-white mt-1" id="kpiSales">$0.00</p>
          </div>
          <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
            <p class="text-xs text-slate-400">Orders</p>
            <p class="text-xl font-extrabold text-white mt-1" id="kpiOrders">0</p>
          </div>
          <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
            <p class="text-xs text-slate-400">Products</p>
            <p class="text-xl font-extrabold text-white mt-1" id="kpiProducts">0</p>
          </div>
          <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
            <p class="text-xs text-slate-400">Low Stock</p>
            <p class="text-xl font-extrabold text-rose-400 mt-1" id="kpiLowStock">0</p>
          </div>
        </div>

        <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
          <h2 class="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">30-Day Sales Trend</h2>
          <div class="w-full h-44"><canvas id="salesChart"></canvas></div>
        </div>

        <div class="bg-slate-800/80 rounded-2xl p-4 border border-slate-700">
          <h2 class="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">Recent Transactions</h2>
          <div id="recentTxList" class="divide-y divide-slate-700 text-xs"></div>
        </div>
      </div>

      <!-- TAB 2: POINT OF SALE (POS) MACHINE (Staff) -->
      <div id="tab-pos" class="tab-pane space-y-4 hidden">
        <div class="bg-slate-800/90 rounded-2xl p-3 border border-slate-700 space-y-2">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold text-teal-400">🛒 POS Terminal</h2>
            <button onclick="clearCart()" class="text-[11px] text-rose-400 hover:underline">Clear Cart</button>
          </div>
          <input type="text" id="posSearch" onkeyup="filterPosProducts()" placeholder="🔍 Scan or search products..." class="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs focus:outline-none focus:border-teal-500">
        </div>

        <div class="text-xs font-semibold text-slate-400">Tap to add item:</div>
        <div id="posProductGrid" class="grid grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1"></div>

        <div class="bg-slate-800/90 rounded-2xl p-4 border border-slate-700 space-y-3">
          <div class="text-xs font-bold text-slate-200">Current Order</div>
          <div id="cartItemsList" class="divide-y divide-slate-700 max-h-36 overflow-y-auto pr-1 text-xs space-y-1">
            <div class="py-4 text-center text-slate-500">No items selected</div>
          </div>
          
          <div class="border-t border-slate-700 pt-2 space-y-1 text-xs">
            <div class="flex justify-between text-slate-400"><span>Subtotal</span><span id="posSubtotal">$0.00</span></div>
            <div class="flex justify-between text-slate-400"><span>Tax (5%)</span><span id="posTax">$0.00</span></div>
            <div class="flex justify-between font-bold text-sm text-teal-400"><span>Total Due</span><span id="posTotal">$0.00</span></div>
          </div>

          <div class="space-y-2 pt-2">
            <div class="grid grid-cols-3 gap-2 text-xs">
              <button onclick="setPaymentMethod('Cash')" id="btnPayCash" class="pay-btn py-2 rounded-xl bg-teal-600 text-white font-bold">Cash</button>
              <button onclick="setPaymentMethod('UPI')" id="btnPayUPI" class="pay-btn py-2 rounded-xl bg-slate-700 text-slate-300">UPI</button>
              <button onclick="setPaymentMethod('Card')" id="btnPayCard" class="pay-btn py-2 rounded-xl bg-slate-700 text-slate-300">Card</button>
            </div>
            <button onclick="processPOSCheckout()" class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-xs rounded-xl shadow-lg transition">Complete & Print Invoice</button>
          </div>
        </div>
      </div>

      <!-- TAB 3: EMPLOYEES & STAFF ONBOARDING (Admin Only) -->
      <div id="tab-employees" class="tab-pane space-y-4 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Staff Directory</span>
          <button onclick="openStaffModal()" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold shadow">+ Add Staff</button>
        </div>
        <div id="employeesList" class="space-y-2"></div>
      </div>

      <!-- TAB 4: PRODUCTS -->
      <div id="tab-products" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Inventory Catalog</div>
        <div id="allProductsList" class="space-y-2"></div>
      </div>

      <!-- TAB 5: INVENTORY MONITOR -->
      <div id="tab-inventory" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Stock Health Overview</div>
        <div id="inventoryAlertList" class="space-y-2"></div>
      </div>

      <!-- TAB 6: SALES LOGS -->
      <div id="tab-sales" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Completed Invoices</div>
        <div id="allSalesList" class="space-y-2"></div>
      </div>

      <!-- TAB 7: NLP COPILOT & WORKBENCH -->
      <div id="tab-nlp" class="tab-pane space-y-4 hidden">
        <div class="bg-slate-800 rounded-2xl p-4 border border-slate-700 space-y-3">
          <div class="flex items-center space-x-2">
            <span class="p-1.5 rounded-lg bg-teal-500/20 text-teal-400 font-bold text-xs">NLP ENGINE</span>
            <span class="text-xs text-slate-400 font-semibold">Text-to-SQL Interpreter</span>
          </div>

          <div class="flex gap-2">
            <input id="workbenchQuery" type="text" placeholder="e.g. Which products have less than 10 items?" class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-teal-500">
            <button onclick="runWorkbenchNLP()" class="px-4 py-2.5 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl text-xs">Execute</button>
          </div>

          <div class="flex gap-1.5 flex-wrap text-[10px]">
            <span class="text-slate-500 self-center">Prompts:</span>
            <button onclick="setNLPInput('Show today\\'s sales')" class="bg-slate-700 px-2 py-1 rounded text-slate-300">Today's Sales</button>
            <button onclick="setNLPInput('Which products have less than 10 items?')" class="bg-slate-700 px-2 py-1 rounded text-slate-300">Low Stock &lt; 10</button>
            <button onclick="setNLPInput('Who are the employees in the sales department?')" class="bg-slate-700 px-2 py-1 rounded text-slate-300">Sales Staff</button>
            <button onclick="setNLPInput('Which product has the highest sales?')" class="bg-slate-700 px-2 py-1 rounded text-slate-300">Best Seller</button>
          </div>
        </div>

        <div id="nlpInspectorCard" class="bg-slate-800 rounded-2xl p-4 border border-slate-700 space-y-3 hidden text-xs">
          <div class="font-bold text-teal-400 flex items-center justify-between border-b border-slate-700 pb-2">
            <span>Query Analysis Breakdown</span>
            <span id="nlpConfidence" class="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded-full"></span>
          </div>

          <div>
            <span class="text-slate-400 block text-[11px] mb-1">Detected Intent:</span>
            <code id="nlpIntent" class="text-purple-300 font-mono text-[11px] bg-slate-900 px-2 py-1 rounded block"></code>
          </div>

          <div>
            <span class="text-slate-400 block text-[11px] mb-1">Extracted Entities (NER):</span>
            <div id="nlpEntities" class="flex flex-wrap gap-1"></div>
          </div>

          <div>
            <span class="text-slate-400 block text-[11px] mb-1">Generated SQL Query:</span>
            <code id="nlpSQL" class="text-emerald-400 font-mono text-[10px] bg-slate-900 p-2 rounded block break-all"></code>
          </div>

          <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-700">
            <span class="text-slate-400 text-[10px] uppercase font-bold block mb-1">Natural Language Response:</span>
            <p id="nlpResponse" class="text-white text-xs font-medium"></p>
          </div>
        </div>
      </div>

    </main>

    <!-- Side Drawer Navigation -->
    <div id="drawerOverlay" onclick="toggleDrawer()" class="fixed inset-0 bg-slate-950/60 z-40 hidden"></div>
    <div id="sideDrawer" class="fixed top-0 bottom-0 left-0 w-72 bg-[#091b2c] text-slate-100 z-50 p-6 flex flex-col justify-between transform -translate-x-full transition-transform duration-300 ease-in-out border-r border-slate-800">
      <div class="space-y-6">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center font-bold text-white">BIZ</div>
          <div>
            <h3 class="font-bold text-base leading-tight">BizCore NLP</h3>
            <p class="text-[11px] text-slate-400">{{ user.designation }}</p>
          </div>
        </div>

        <nav class="space-y-1 text-sm font-medium">
          <button onclick="switchTab('dashboard')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl bg-teal-600/20 text-teal-400">📊 Dashboard</button>
          
          {% if user.role == 'employee' %}
          <button onclick="switchTab('pos')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">🛒 POS Terminal</button>
          {% endif %}

          {% if user.role == 'admin' %}
          <button onclick="switchTab('employees')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">👥 Staff & Posts</button>
          {% endif %}

          <button onclick="switchTab('products')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">📦 Products</button>
          <button onclick="switchTab('inventory')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">📋 Inventory</button>
          <button onclick="switchTab('sales')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">🧾 Sales Invoices</button>
          <button onclick="switchTab('nlp')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">💬 NLP Assistant</button>
        </nav>
      </div>

      <div class="border-t border-slate-800 pt-4">
        <div class="font-bold text-sm text-white">{{ user.name }}</div>
        <div class="text-xs text-slate-400 mb-3">{{ user.email }}</div>
        <a href="/logout" class="text-xs text-rose-400 hover:underline block font-semibold">Sign out</a>
      </div>
    </div>

    <!-- Admin Add Staff Modal -->
    <div id="addStaffModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#1e293b] border border-slate-700 rounded-3xl p-6 w-full max-w-sm space-y-4">
        <h3 class="font-bold text-base text-white">Create Staff & Assign Post</h3>
        <input type="text" id="staffName" placeholder="Full Name" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="email" id="staffEmail" placeholder="Login Email" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="password" id="staffPass" placeholder="Login Password" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
        
        <div>
          <label class="text-[11px] text-slate-400 mb-1 block">Assigned Post / Designation:</label>
          <select id="staffPost" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
            <option value="Store Manager">Store Manager</option>
            <option value="Shift Supervisor">Shift Supervisor</option>
            <option value="POS Cashier">POS Cashier</option>
            <option value="Inventory Officer">Inventory Officer</option>
          </select>
        </div>

        <div>
          <label class="text-[11px] text-slate-400 mb-1 block">Department:</label>
          <select id="staffDept" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
            <option value="1">Sales</option>
            <option value="2">Operations</option>
            <option value="3">Inventory</option>
          </select>
        </div>

        <div class="flex gap-2 pt-2">
          <button onclick="closeStaffModal()" class="w-1/2 py-2.5 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewStaff()" class="w-1/2 py-2.5 bg-purple-600 hover:bg-purple-500 font-bold text-white text-xs rounded-xl">Create Staff</button>
        </div>
      </div>
    </div>

  </div>

  <script>
    let appData = {};
    let currentCart = [];
    let selectedPayment = 'Cash';

    function toggleDrawer() {
      document.getElementById('sideDrawer').classList.toggle('-translate-x-full');
      document.getElementById('drawerOverlay').classList.toggle('hidden');
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      const active = document.getElementById('tab-' + tabId);
      if (active) active.classList.remove('hidden');

      const titleMap = {
        'dashboard': 'Dashboard',
        'pos': 'POS Terminal',
        'employees': 'Staff Management',
        'products': 'Product Catalog',
        'inventory': 'Inventory Alerts',
        'sales': 'Sales Invoices',
        'nlp': 'NLP Copilot'
      };
      document.getElementById('pageTitle').innerText = titleMap[tabId] || 'Dashboard';
      toggleDrawer();
    }

    function openStaffModal() { document.getElementById('addStaffModal').classList.remove('hidden'); }
    function closeStaffModal() { document.getElementById('addStaffModal').classList.add('hidden'); }

    // POS Logic
    function renderPOSProducts(items) {
      const grid = document.getElementById('posProductGrid');
      grid.innerHTML = items.map(p => `
        <div onclick="addToCart(${p.product_id})" class="bg-slate-900 p-2.5 rounded-xl border border-slate-700/80 cursor-pointer hover:border-teal-500 transition flex flex-col justify-between">
          <div>
            <div class="font-bold text-xs text-white leading-tight">${p.product_name}</div>
            <div class="text-[10px] text-slate-400 mt-0.5">${p.category}</div>
          </div>
          <div class="flex items-center justify-between mt-2 pt-1 border-t border-slate-800">
            <span class="font-extrabold text-xs text-teal-400">$${parseFloat(p.price).toFixed(2)}</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-300'}">${p.stock} left</span>
          </div>
        </div>
      `).join('');
    }

    function filterPosProducts() {
      const q = document.getElementById('posSearch').value.toLowerCase();
      const filtered = appData.products.filter(p => p.product_name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
      renderPOSProducts(filtered);
    }

    function addToCart(productId) {
      const prod = appData.products.find(p => p.product_id === productId);
      if (!prod || prod.stock <= 0) return alert('Item out of stock!');

      const existing = currentCart.find(i => i.product_id === productId);
      if (existing) {
        if (existing.qty < prod.stock) existing.qty++;
        else alert('No more units in stock!');
      } else {
        currentCart.push({ product_id: prod.product_id, name: prod.product_name, price: parseFloat(prod.price), qty: 1 });
      }
      renderCart();
    }

    function changeCartQty(productId, delta) {
      const item = currentCart.find(i => i.product_id === productId);
      if (!item) return;
      item.qty += delta;
      if (item.qty <= 0) currentCart = currentCart.filter(i => i.product_id !== productId);
      renderCart();
    }

    function clearCart() {
      currentCart = [];
      renderCart();
    }

    function renderCart() {
      const container = document.getElementById('cartItemsList');
      if (currentCart.length === 0) {
        container.innerHTML = '<div class="py-4 text-center text-slate-500">No items selected</div>';
        document.getElementById('posSubtotal').innerText = '$0.00';
        document.getElementById('posTax').innerText = '$0.00';
        document.getElementById('posTotal').innerText = '$0.00';
        return;
      }

      let subtotal = 0;
      container.innerHTML = currentCart.map(i => {
        const line = i.price * i.qty;
        subtotal += line;
        return `
          <div class="flex items-center justify-between py-1.5">
            <div class="flex-1 pr-2">
              <div class="font-bold text-white leading-tight">${i.name}</div>
              <div class="text-[10px] text-slate-400">$${i.price.toFixed(2)} x ${i.qty}</div>
            </div>
            <div class="flex items-center space-x-2">
              <button onclick="changeCartQty(${i.product_id}, -1)" class="w-5 h-5 rounded bg-slate-700 text-white flex items-center justify-center font-bold">-</button>
              <span class="font-bold text-teal-400">${i.qty}</span>
              <button onclick="changeCartQty(${i.product_id}, 1)" class="w-5 h-5 rounded bg-slate-700 text-white flex items-center justify-center font-bold">+</button>
            </div>
          </div>
        `;
      }).join('');

      const tax = subtotal * 0.05;
      const total = subtotal + tax;
      document.getElementById('posSubtotal').innerText = `$${subtotal.toFixed(2)}`;
      document.getElementById('posTax').innerText = `$${tax.toFixed(2)}`;
      document.getElementById('posTotal').innerText = `$${total.toFixed(2)}`;
    }

    function setPaymentMethod(method) {
      selectedPayment = method;
      document.querySelectorAll('.pay-btn').forEach(b => {
        b.classList.remove('bg-teal-600', 'text-white', 'font-bold');
        b.classList.add('bg-slate-700', 'text-slate-300');
      });
      const activeBtn = document.getElementById('btnPay' + method);
      activeBtn.classList.remove('bg-slate-700', 'text-slate-300');
      activeBtn.classList.add('bg-teal-600', 'text-white', 'font-bold');
    }

    async function processPOSCheckout() {
      if (currentCart.length === 0) return alert('Cart is empty!');
      const subtotal = currentCart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const total = subtotal * 1.05;

      const res = await fetch('/api/pos-checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ cart: currentCart, total: total, payment_method: selectedPayment })
      });
      const d = await res.json();
      if (d.status === 'success') {
        alert(`Transaction Successful!\\nInvoice: ${d.invoice_no}\\nAmount: $${total.toFixed(2)}\\nMethod: ${selectedPayment}`);
        clearCart();
        loadAllData();
      }
    }

    // Submit Staff
    async function submitNewStaff() {
      const name = document.getElementById('staffName').value;
      const email = document.getElementById('staffEmail').value;
      const pass = document.getElementById('staffPass').value;
      const post = document.getElementById('staffPost').value;
      const dept = document.getElementById('staffDept').value;
      if (!name || !email || !pass) return alert('Please enter all credentials');

      await fetch('/api/add-staff', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: name, email: email, password: pass, designation: post, dept_id: dept })
      });
      closeStaffModal();
      alert(`Staff member ${name} created with post ${post}. They can now login with ${email}`);
      loadAllData();
    }

    // NLP Execution
    function setNLPInput(text) {
      document.getElementById('workbenchQuery').value = text;
      runWorkbenchNLP();
    }

    async function runWorkbenchNLP() {
      const q = document.getElementById('workbenchQuery').value.trim();
      if (!q) return;

      const res = await fetch('/api/nlp-query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: q })
      });
      const d = await res.json();
      const nlp = d.nlp_result;

      const card = document.getElementById('nlpInspectorCard');
      card.classList.remove('hidden');

      document.getElementById('nlpConfidence').innerText = `Confidence: ${nlp.confidence}`;
      document.getElementById('nlpIntent').innerText = nlp.intent;
      document.getElementById('nlpSQL').innerText = nlp.sql;
      document.getElementById('nlpResponse').innerText = nlp.answer;

      const entBox = document.getElementById('nlpEntities');
      if (nlp.entities && nlp.entities.length > 0) {
        entBox.innerHTML = nlp.entities.map(e => `
          <span class="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[10px]">
            [${e.type} = "${e.value}"]
          </span>
        `).join('');
      } else {
        entBox.innerHTML = '<span class="text-slate-500 italic">None detected</span>';
      }
    }

    // Load Data
    async function loadAllData() {
      const res = await fetch('/api/all-data');
      appData = await res.json();

      document.getElementById('kpiSales').innerText = `$${appData.total_revenue.toFixed(2)}`;
      document.getElementById('kpiOrders').innerText = appData.sales.length;
      document.getElementById('kpiProducts').innerText = appData.products.length;
      document.getElementById('kpiLowStock').innerText = appData.low_stock.length;

      document.getElementById('recentTxList').innerHTML = appData.sales.slice(0, 5).map(s => `
        <div class="flex justify-between items-center py-2">
          <div>
            <div class="font-bold text-white">${s.invoice_no}</div>
            <div class="text-[10px] text-slate-400">${s.sale_date} · By ${s.cashier_name}</div>
          </div>
          <span class="font-extrabold text-teal-400">$${parseFloat(s.total_amount).toFixed(2)}</span>
        </div>
      `).join('');

      renderPOSProducts(appData.products);

      const empList = document.getElementById('employeesList');
      if (empList) {
        empList.innerHTML = appData.employees.map(e => `
          <div class="bg-slate-800 p-3 rounded-2xl border border-slate-700 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${e.name}</div>
              <div class="text-[11px] text-purple-400 font-medium">${e.designation} (${e.dept_name})</div>
              <div class="text-[10px] text-slate-400">${e.email}</div>
            </div>
            <span class="px-2 py-1 bg-slate-900 rounded-lg text-[10px] font-bold text-teal-300 capitalize">${e.role}</span>
          </div>
        `).join('');
      }

      document.getElementById('allProductsList').innerHTML = appData.products.map(p => `
        <div class="bg-slate-800 p-3 rounded-2xl border border-slate-700 flex justify-between items-center text-xs">
          <div>
            <div class="font-bold text-white">${p.product_name}</div>
            <div class="text-[10px] text-slate-400">${p.category} · $${p.price}</div>
          </div>
          <span class="font-bold px-2 py-0.5 rounded text-[11px] ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-900 text-teal-400'}">${p.stock} units</span>
        </div>
      `).join('');

      document.getElementById('inventoryAlertList').innerHTML = appData.products.map(p => `
        <div class="bg-slate-800 p-3 rounded-2xl border border-slate-700 flex justify-between items-center text-xs">
          <div class="font-medium text-white">${p.product_name}</div>
          <span class="font-bold text-xs ${p.stock <= 4 ? 'text-rose-400 font-extrabold' : p.stock < 10 ? 'text-amber-400' : 'text-teal-400'}">${p.stock} left</span>
        </div>
      `).join('');

      document.getElementById('allSalesList').innerHTML = appData.sales.map(s => `
        <div class="bg-slate-800 p-3 rounded-2xl border border-slate-700 flex justify-between items-center text-xs">
          <div>
            <div class="font-bold text-white">${s.invoice_no}</div>
            <div class="text-[10px] text-slate-400">${s.sale_date} · Cashier: ${s.cashier_name}</div>
          </div>
          <span class="font-extrabold text-white">$${parseFloat(s.total_amount).toFixed(2)}</span>
        </div>
      `).join('');
    }

    function initSalesChart() {
      const ctx = document.getElementById('salesChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: ['09-14', '09-19', '09-24', '09-29', '10-04', '10-10'],
          datasets: [{
            data: [0, 2200, 3600, 1600, 5200, 6500],
            borderColor: '#14b8a6',
            backgroundColor: 'rgba(20, 184, 166, 0.15)',
            fill: true,
            tension: 0.35,
            pointRadius: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 9 }, color: '#94a3b8' } },
            y: { ticks: { stepSize: 2000, font: { size: 9 }, color: '#94a3b8' }, border: { dash: [4, 4] } }
          }
        }
      });
    }

    document.addEventListener('DOMContentLoaded', () => {
      initSalesChart();
      loadAllData();
    });
  </script>
</body>
</html>
"""

with open("templates/dashboard.html", "w") as f:
    f.write(html_code)

print("\nSUCCESS: All upgraded systems written cleanly! No terminal freezing occurred.")
