import os
import pymysql

# ==========================================
# 1. DATABASE SCHEMA & TABLE MIGRATIONS
# ==========================================
def upgrade_database():
    conn = pymysql.connect(
        host="localhost",
        user="biz_user",
        password="biz_pass123"
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS business_management;")
    cursor.execute("USE business_management;")

    # Departments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INT AUTO_INCREMENT PRIMARY KEY,
        dept_name VARCHAR(100) UNIQUE NOT NULL
    );
    """)

    # Users
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

    # Employees
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

    # Products (with SKU, Cost Price, Selling Price)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        sku VARCHAR(50) UNIQUE NOT NULL,
        product_name VARCHAR(150) NOT NULL,
        category VARCHAR(100),
        cost_price DECIMAL(10, 2) DEFAULT 0.00,
        price DECIMAL(10, 2) NOT NULL,
        stock INT DEFAULT 0
    );
    """)

    # Suppliers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INT AUTO_INCREMENT PRIMARY KEY,
        supplier_name VARCHAR(150) NOT NULL,
        contact_person VARCHAR(100),
        phone VARCHAR(20),
        email VARCHAR(100),
        address TEXT
    );
    """)

    # Purchases (Stock Inward)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        purchase_id INT AUTO_INCREMENT PRIMARY KEY,
        supplier_id INT,
        invoice_ref VARCHAR(100),
        purchase_date DATE NOT NULL,
        total_amount DECIMAL(10, 2) NOT NULL,
        notes VARCHAR(255),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
    );
    """)

    # Purchase Line Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_items (
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        purchase_id INT,
        product_id INT,
        quantity INT NOT NULL,
        unit_cost DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (purchase_id) REFERENCES purchases(purchase_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)

    # Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) UNIQUE,
        email VARCHAR(100)
    );
    """)

    # Sales Invoices (Commercial POS Fields)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        invoice_no VARCHAR(50) NOT NULL,
        sale_date DATE NOT NULL,
        customer_name VARCHAR(100) DEFAULT 'Walk-in Customer',
        subtotal DECIMAL(10, 2) NOT NULL,
        discount DECIMAL(10, 2) DEFAULT 0.00,
        tax DECIMAL(10, 2) DEFAULT 0.00,
        total_amount DECIMAL(10, 2) NOT NULL,
        tendered DECIMAL(10, 2) DEFAULT 0.00,
        change_due DECIMAL(10, 2) DEFAULT 0.00,
        payment_method VARCHAR(50) DEFAULT 'Cash',
        cashier_name VARCHAR(100) DEFAULT 'Staff',
        status ENUM('completed', 'held', 'voided') DEFAULT 'completed'
    );
    """)

    # Sale Items
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

    # Add columns safely if tables existed prior
    for query in [
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(50) DEFAULT 'SKU-001';",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price DECIMAL(10, 2) DEFAULT 0.00;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS designation VARCHAR(100) DEFAULT 'Staff';",
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS status ENUM('completed', 'held', 'voided') DEFAULT 'completed';",
        "ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_name VARCHAR(100) DEFAULT 'Walk-in Customer';"
    ]:
        try:
            cursor.execute(query)
        except Exception:
            pass

    # Populate Initial Data
    cursor.execute("SELECT COUNT(*) FROM departments;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT IGNORE INTO departments (dept_id, dept_name) VALUES (1, 'Sales & Counter'), (2, 'Store Operations'), (3, 'Inventory & Procurement'), (4, 'Accounts & Finance');")

    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (name, email, password, role, designation) VALUES 
        ('Admin User', 'admin@bizcore.dev', 'admin123', 'admin', 'Store General Manager'),
        ('Priya Nair', 'employee@bizcore.dev', 'employee123', 'employee', 'Head Cashier');
        """)
        cursor.execute("INSERT INTO employees (name, email, designation, dept_id, user_id) VALUES ('Priya Nair', 'employee@bizcore.dev', 'Head Cashier', 1, 2);")

    cursor.execute("SELECT COUNT(*) FROM products;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO products (sku, product_name, category, cost_price, price, stock) VALUES
        ('ELEC-101', 'Lenovo ThinkPad E14 Laptop', 'Electronics', 850.00, 1100.00, 6),
        ('ELEC-102', 'MacBook Air M2 Laptop', 'Electronics', 980.00, 1199.00, 4),
        ('DISP-201', 'LG 27\" 4K Monitor', 'Displays', 320.00, 450.00, 9),
        ('ACC-301', 'Mechanical Keyboard', 'Accessories', 75.00, 120.00, 7),
        ('AUD-401', 'Noise-Cancelling Headset', 'Audio', 130.00, 200.00, 3),
        ('OFF-501', 'Toner Cartridge 85A', 'Office Supplies', 40.00, 65.00, 8),
        ('NET-601', '24-Port Network Switch', 'Networking', 240.00, 350.00, 5),
        ('FURN-701', 'Standing Desk', 'Furniture', 380.00, 550.00, 2),
        ('DISP-202', 'Dell UltraSharp 32\"', 'Displays', 540.00, 720.00, 18),
        ('ACC-302', 'Logitech MX Master 3S', 'Accessories', 65.00, 99.00, 25),
        ('FURN-702', 'Ergonomic Office Chair', 'Furniture', 210.00, 320.00, 14),
        ('STOR-801', 'Samsung T7 1TB SSD', 'Storage', 85.00, 130.00, 22);
        """)

    cursor.execute("SELECT COUNT(*) FROM suppliers;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO suppliers (supplier_name, contact_person, phone, email, address) VALUES
        ('Apex Hardware Distributors', 'Ramesh Rao', '+91 98450 11223', 'orders@apexdistro.com', 'Warehouse 4, Electronic City, Bangalore'),
        ('Prime Office & Tech Supplies', 'Anand Verma', '+91 98711 33445', 'sales@primetech.in', 'Plot 12, Industrial Area, Mangalore');
        """)

    cursor.execute("SELECT COUNT(*) FROM customers;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO customers (name, phone, email) VALUES
        ('Walk-in Customer', '0000000000', 'walkin@store.internal'),
        ('Arun Varma', '+91 98765 43210', 'arun.varma@gmail.com'),
        ('Divya Nair', '+91 98123 45678', 'divya.nair@outlook.com');
        """)

    conn.commit()
    conn.close()
    print("Database upgrade completed successfully.")

upgrade_database()

# ==========================================
# 2. WRITE UPGRADED app.py
# ==========================================
app_code = """from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pymysql.cursors
from nlp_engine.parser import NLPQueryParser

app = Flask(__name__)
app.secret_key = "bizcore_enterprise_secret_key"

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
                        'designation': user.get('designation', 'Staff')
                    }
                    return redirect(url_for('dashboard'))
                return render_template('login.html', error="Invalid credentials.")
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

# Full Business Data Stream
@app.route('/api/master-data')
def get_master_data():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Products
            cursor.execute("SELECT * FROM products ORDER BY product_id DESC")
            products = cursor.fetchall()
            for p in products:
                p['cost_price'] = float(p.get('cost_price') or 0.0)
                p['price'] = float(p['price'])

            # Low Stock
            cursor.execute("SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC")
            low_stock = cursor.fetchall()

            # Sales
            cursor.execute("SELECT * FROM sales ORDER BY sale_id DESC")
            sales = cursor.fetchall()
            for s in sales:
                s['sale_date'] = s['sale_date'].strftime('%Y-%m-%d')
                s['total_amount'] = float(s['total_amount'])
                s['subtotal'] = float(s.get('subtotal') or 0.0)

            # Customers
            cursor.execute("SELECT * FROM customers ORDER BY name ASC")
            customers = cursor.fetchall()

            # Employees & Depts
            cursor.execute(\"\"\"
                SELECT e.employee_id, e.name, e.email, e.designation, d.dept_name, u.role
                FROM employees e
                LEFT JOIN departments d ON e.dept_id = d.dept_id
                LEFT JOIN users u ON e.user_id = u.user_id
                ORDER BY e.employee_id DESC
            \"\"\")
            employees = cursor.fetchall()

            cursor.execute("SELECT * FROM departments ORDER BY dept_name ASC")
            departments = cursor.fetchall()

            # Suppliers
            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_name ASC")
            suppliers = cursor.fetchall()

            # Purchases with Supplier details
            cursor.execute(\"\"\"
                SELECT p.*, s.supplier_name 
                FROM purchases p 
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id 
                ORDER BY p.purchase_id DESC
            \"\"\")
            purchases = cursor.fetchall()
            for pur in purchases:
                pur['purchase_date'] = pur['purchase_date'].strftime('%Y-%m-%d')
                pur['total_amount'] = float(pur['total_amount'])

            # Metrics
            cursor.execute("SELECT IFNULL(SUM(total_amount), 0) AS rev FROM sales WHERE status = 'completed'")
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

# 1. ADD / CREATE DEPARTMENT
@app.route('/api/add-department', methods=['POST'])
def add_department():
    if session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    name = (request.get_json() or {}).get('dept_name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO departments (dept_name) VALUES (%s)", (name,))
            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# 2. CREATE STAFF WITH CUSTOM POST & DEPT
@app.route('/api/add-staff', methods=['POST'])
def add_staff():
    if session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Handle dynamic department creation on the fly
            dept_id = data.get('dept_id')
            if data.get('custom_dept'):
                cursor.execute("INSERT IGNORE INTO departments (dept_name) VALUES (%s)", (data['custom_dept'],))
                cursor.execute("SELECT dept_id FROM departments WHERE dept_name = %s", (data['custom_dept'],))
                dept_id = cursor.fetchone()['dept_id']

            # Post / Designation
            post = data.get('custom_designation') or data.get('designation', 'Store Staff')

            # Create User Login
            cursor.execute(\"\"\"
                INSERT INTO users (name, email, password, role, designation)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (data['name'], data['email'], data['password'], data.get('role', 'employee'), post))
            user_id = cursor.lastrowid

            # Create Employee Record
            cursor.execute(\"\"\"
                INSERT INTO employees (name, email, designation, dept_id, user_id)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (data['name'], data['email'], post, dept_id, user_id))
            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# 3. ADD PRODUCT
@app.route('/api/add-product', methods=['POST'])
def add_product():
    if session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(\"\"\"
                INSERT INTO products (sku, product_name, category, cost_price, price, stock)
                VALUES (%s, %s, %s, %s, %s, %s)
            \"\"\", (d['sku'], d['product_name'], d['category'], float(d.get('cost_price', 0)), float(d['price']), int(d.get('stock', 0))))
            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# 4. ADD SUPPLIER
@app.route('/api/add-supplier', methods=['POST'])
def add_supplier():
    if session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(\"\"\"
                INSERT INTO suppliers (supplier_name, contact_person, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (d['supplier_name'], d.get('contact_person'), d.get('phone'), d.get('email'), d.get('address')))
            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# 5. ENTER PURCHASE (STOCK INWARD) -> INCREMENTS INVENTORY
@app.route('/api/add-purchase', methods=['POST'])
def add_purchase():
    if session['user']['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    d = request.get_json() or {}
    items = d.get('items', [])
    if not items:
        return jsonify({'error': 'No items in purchase'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Create Purchase Order Record
            cursor.execute(\"\"\"
                INSERT INTO purchases (supplier_id, invoice_ref, purchase_date, total_amount, notes)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (d['supplier_id'], d.get('invoice_ref', 'PUR-REF'), d.get('purchase_date'), float(d['total_amount']), d.get('notes', 'Inward Stock')))
            purchase_id = cursor.lastrowid

            # Add lines & INCREMENT Stock in Products table
            for it in items:
                cursor.execute(\"\"\"
                    INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_cost)
                    VALUES (%s, %s, %s, %s)
                \"\"\", (purchase_id, it['product_id'], int(it['quantity']), float(it['unit_cost'])))

                # Commercial Logic: Inward shipment increments stock
                cursor.execute(\"\"\"
                    UPDATE products 
                    SET stock = stock + %s, cost_price = %s 
                    WHERE product_id = %s
                \"\"\", (int(it['quantity']), float(it['unit_cost']), it['product_id']))

            conn.commit()
            return jsonify({'status': 'success'})
    finally:
        conn.close()

# 6. COMMERCIAL POS CHECKOUT (With discounts, change math, tender modes)
@app.route('/api/pos-checkout', methods=['POST'])
def pos_checkout():
    d = request.get_json() or {}
    cart = d.get('cart', [])
    if not cart:
        return jsonify({'error': 'Empty cart'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM sales")
            inv_no = f"INV-{5000 + cursor.fetchone()['cnt'] + 1}"

            subtotal = float(d.get('subtotal', 0))
            discount = float(d.get('discount', 0))
            tax = float(d.get('tax', 0))
            total = float(d.get('total', 0))
            tendered = float(d.get('tendered', total))
            change = float(d.get('change_due', 0))
            method = d.get('payment_method', 'Cash')
            customer = d.get('customer_name', 'Walk-in Customer')
            cashier = session['user']['name']
            status = d.get('status', 'completed')

            cursor.execute(\"\"\"
                INSERT INTO sales (invoice_no, sale_date, customer_name, subtotal, discount, tax, total_amount, tendered, change_due, payment_method, cashier_name, status)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (inv_no, customer, subtotal, discount, tax, total, tendered, change, method, cashier, status))
            sale_id = cursor.lastrowid

            if status == 'completed':
                for it in cart:
                    cursor.execute(\"\"\"
                        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
                        VALUES (%s, %s, %s, %s)
                    \"\"\", (sale_id, it['product_id'], int(it['qty']), float(it['price'])))

                    # Deduct inventory
                    cursor.execute(\"\"\"
                        UPDATE products SET stock = stock - %s WHERE product_id = %s
                    \"\"\", (int(it['qty']), it['product_id']))

            conn.commit()
            return jsonify({'status': 'success', 'invoice_no': inv_no})
    finally:
        conn.close()

# 7. NLP ASSISTANT
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

# ==========================================
# 3. WRITE UPGRADED dashboard.html
# ==========================================
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BizCore NLP - Enterprise Commerce POS & Management</title>
  <link rel="manifest" href="/static/manifest.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    .pos-btn { @apply bg-slate-800 hover:bg-slate-700 active:bg-teal-600 active:text-white rounded-xl font-bold transition flex items-center justify-center select-none shadow text-xs; }
    .fn-btn { @apply bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 px-1 text-[11px] rounded-lg font-semibold text-center border border-slate-700 shadow-sm transition; }
    .tender-btn { @apply py-2 rounded-xl text-xs font-bold transition border border-slate-700; }
  </style>
</head>
<body class="bg-[#0b1322] text-slate-100 min-h-screen font-sans flex flex-col items-center">

  <div class="w-full max-w-lg bg-[#141f32] min-h-screen shadow-2xl relative pb-12 flex flex-col border-x border-slate-800">
    <!-- Top Bar -->
    <header class="px-5 py-4 flex items-center justify-between border-b border-slate-800 bg-[#141f32] sticky top-0 z-40">
      <div class="flex items-center space-x-3">
        <button onclick="toggleDrawer()" class="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
        <div>
          <h1 id="pageTitle" class="text-base font-bold text-white leading-tight">POS Terminal</h1>
          <p class="text-[11px] text-teal-400 font-medium">{{ user.designation }}</p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold {% if user.role == 'admin' %}bg-purple-500/20 text-purple-300 border border-purple-500/30{% else %}bg-teal-500/20 text-teal-300 border border-teal-500/30{% endif %} capitalize">
          {{ user.role }}
        </span>
      </div>
    </header>

    <!-- Main Views Container -->
    <main class="p-3.5 space-y-4 flex-1">

      <!-- ==================================================== -->
      <!-- SCREEN 1: COMMERCIAL POS TERMINAL (Like Hardware POS) -->
      <!-- ==================================================== -->
      <div id="tab-pos" class="tab-pane space-y-3">
        
        <!-- SKU Scan / Search & Customer Select -->
        <div class="bg-slate-900/90 rounded-2xl p-3 border border-slate-800 space-y-2">
          <div class="flex gap-2">
            <input type="text" id="posSkuInput" placeholder="Enter SKU / Scan Barcode or Item..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500 font-mono">
            <button onclick="searchAndAddSku()" class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold">Pick</button>
          </div>
          <div class="flex items-center justify-between text-[11px] text-slate-400 pt-1">
            <span>Customer:</span>
            <select id="posCustomerSelect" class="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-[11px] text-slate-200">
              <option value="Walk-in Customer">Walk-in Customer (General)</option>
            </select>
          </div>
        </div>

        <!-- Category Filter Tabs -->
        <div id="posCategoryTabs" class="flex gap-1.5 overflow-x-auto pb-1 text-[11px] scrollbar-none">
          <button onclick="filterPosCategory('ALL')" class="px-3 py-1.5 rounded-xl bg-teal-600 text-white font-bold whitespace-nowrap">All Items</button>
        </div>

        <!-- Quick Item Buttons Grid -->
        <div id="posGridItems" class="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto pr-1"></div>

        <!-- Sales Order Table (Real Commerce Receipt View) -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow">
          <div class="bg-slate-800/80 px-3 py-1.5 grid grid-cols-12 text-[10px] font-bold text-slate-300 uppercase">
            <span class="col-span-5">Item Sold</span>
            <span class="col-span-2 text-center">Qty</span>
            <span class="col-span-2 text-right">Price</span>
            <span class="col-span-3 text-right">Total</span>
          </div>
          <div id="posOrderLines" class="divide-y divide-slate-800 max-h-44 overflow-y-auto text-xs min-h-[100px]">
            <div class="py-8 text-center text-slate-500 text-xs">No items rung up yet</div>
          </div>
        </div>

        <!-- POS Operation Utility Functions (Like the Picture) -->
        <div class="grid grid-cols-4 gap-1.5">
          <button onclick="promptChangeQty()" class="fn-btn">Change Qty</button>
          <button onclick="promptDiscount()" class="fn-btn">Discount %</button>
          <button onclick="voidSelectedItem()" class="fn-btn text-amber-400">Void Item</button>
          <button onclick="voidEntireSale()" class="fn-btn text-rose-400">Void Sale</button>
          <button onclick="holdCurrentOrder()" class="fn-btn text-teal-300">Hold Order</button>
          <button onclick="retrieveHeldOrder()" class="fn-btn text-blue-300">Retrieve</button>
          <button onclick="promptCustomPrice()" class="fn-btn">Price Override</button>
          <button onclick="clearPosAll()" class="fn-btn text-slate-400">Clear</button>
        </div>

        <!-- Financial Totals Summary -->
        <div class="bg-slate-900/90 rounded-2xl p-3 border border-slate-800 space-y-1.5 text-xs">
          <div class="flex justify-between text-slate-400"><span>Sub Total:</span><span id="posSubtotal" class="font-mono">$0.00</span></div>
          <div class="flex justify-between text-slate-400"><span>Discount:</span><span id="posDiscountAmount" class="font-mono text-emerald-400">-$0.00</span></div>
          <div class="flex justify-between text-slate-400"><span>Tax (5%):</span><span id="posTax" class="font-mono">$0.00</span></div>
          <div class="flex justify-between text-base font-extrabold text-teal-400 border-t border-slate-800 pt-1">
            <span>Balance Due:</span><span id="posBalanceDue" class="font-mono">$0.00</span>
          </div>
          <div class="flex justify-between text-amber-300 font-bold text-xs pt-0.5">
            <span>Change Return:</span><span id="posChangeDue" class="font-mono">$0.00</span>
          </div>
        </div>

        <!-- Quick Cash Tender & Multi-Payment Modes -->
        <div class="space-y-2">
          <div class="grid grid-cols-5 gap-1.5 text-[11px]">
            <button onclick="tenderExactAmount()" class="tender-btn bg-slate-800 text-teal-300 hover:bg-slate-700">Exact</button>
            <button onclick="tenderPresetCash(10)" class="tender-btn bg-slate-800 text-slate-200 hover:bg-slate-700">$10</button>
            <button onclick="tenderPresetCash(20)" class="tender-btn bg-slate-800 text-slate-200 hover:bg-slate-700">$20</button>
            <button onclick="tenderPresetCash(50)" class="tender-btn bg-slate-800 text-slate-200 hover:bg-slate-700">$50</button>
            <button onclick="tenderPresetCash(100)" class="tender-btn bg-slate-800 text-slate-200 hover:bg-slate-700">$100</button>
          </div>

          <div class="grid grid-cols-4 gap-1.5">
            <button onclick="setTenderMode('Cash')" id="tndCash" class="tender-mode py-2 rounded-xl text-xs font-bold bg-teal-600 text-white">Cash</button>
            <button onclick="setTenderMode('Card')" id="tndCard" class="tender-mode py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">Card</button>
            <button onclick="setTenderMode('UPI')" id="tndUPI" class="tender-mode py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">UPI</button>
            <button onclick="setTenderMode('Check')" id="tndCheck" class="tender-mode py-2 rounded-xl text-xs font-bold bg-slate-800 text-slate-300">Check</button>
          </div>

          <button onclick="executePOSCheckout()" class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 font-extrabold text-white text-sm rounded-2xl shadow-lg transition flex items-center justify-center gap-2">
            <span>Complete Transaction & Print Receipt</span>
          </button>
        </div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 2: ADMIN STAFF & POSTS ASSIGNMENT             -->
      <!-- ==================================================== -->
      <div id="tab-employees" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Staff Personnel & Posts</span>
          <div class="flex gap-2">
            <button onclick="openModal('addDeptModal')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-xl text-xs font-semibold border border-slate-700">+ New Dept</button>
            <button onclick="openModal('addStaffModal')" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold shadow">+ Add Staff</button>
          </div>
        </div>
        <div id="employeesList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 3: PRODUCT CATALOG (Admin Product Adding)    -->
      <!-- ==================================================== -->
      <div id="tab-products" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Items Catalog</span>
          {% if user.role == 'admin' %}
          <button onclick="openModal('addProductModal')" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold shadow">+ Add Product</button>
          {% endif %}
        </div>
        <div id="productsMasterList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 4: SUPPLIERS DIRECTORY                        -->
      <!-- ==================================================== -->
      <div id="tab-suppliers" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Registered Suppliers</span>
          {% if user.role == 'admin' %}
          <button onclick="openModal('addSupplierModal')" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold shadow">+ Add Supplier</button>
          {% endif %}
        </div>
        <div id="suppliersMasterList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 5: PURCHASES (Stock Inward Entry)            -->
      <!-- ==================================================== -->
      <div id="tab-purchases" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Stock Inward / Purchases</span>
          {% if user.role == 'admin' %}
          <button onclick="openModal('addPurchaseModal')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow">+ Inward Stock</button>
          {% endif %}
        </div>
        <div id="purchasesMasterList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 6: INVENTORY MONITOR                          -->
      <!-- ==================================================== -->
      <div id="tab-inventory" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Live Stock Levels</div>
        <div id="inventoryAlertList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 7: SALES INVOICES ARCHIVE                    -->
      <!-- ==================================================== -->
      <div id="tab-sales" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Past Invoices Log</div>
        <div id="allSalesList" class="space-y-2"></div>
      </div>

      <!-- ==================================================== -->
      <!-- SCREEN 8: NLP NATURAL LANGUAGE COPILOT              -->
      <!-- ==================================================== -->
      <div id="tab-nlp" class="tab-pane space-y-3 hidden">
        <div class="bg-slate-900 rounded-2xl p-4 border border-slate-800 space-y-3">
          <div class="flex items-center space-x-2">
            <span class="p-1 rounded-md bg-teal-500/20 text-teal-400 font-bold text-[10px]">NLP CORE</span>
            <span class="text-xs text-slate-400 font-medium">Ask questions in plain English</span>
          </div>
          <div class="flex gap-2">
            <input id="nlpQueryInput" type="text" placeholder="e.g. Which products have less than 10 items?" class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500">
            <button onclick="runNLP()" class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl text-xs">Ask</button>
          </div>
          <div class="flex gap-1.5 flex-wrap text-[10px]">
            <span class="text-slate-500 self-center">Try:</span>
            <button onclick="triggerPrompt('Show today\\'s sales')" class="bg-slate-800 px-2 py-1 rounded text-slate-300">Today's Sales</button>
            <button onclick="triggerPrompt('Which products have less than 10 items?')" class="bg-slate-800 px-2 py-1 rounded text-slate-300">Stock &lt; 10</button>
            <button onclick="triggerPrompt('Who are the employees in the sales department?')" class="bg-slate-800 px-2 py-1 rounded text-slate-300">Sales Staff</button>
            <button onclick="triggerPrompt('Which product has the highest sales?')" class="bg-slate-800 px-2 py-1 rounded text-slate-300">Top Product</button>
          </div>
        </div>

        <div id="nlpInspectorCard" class="bg-slate-900 rounded-2xl p-4 border border-slate-800 space-y-3 hidden text-xs">
          <div class="font-bold text-teal-400 flex items-center justify-between border-b border-slate-800 pb-2">
            <span>Query Inspection & Mapping</span>
            <span id="nlpConf" class="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded-full"></span>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px] mb-0.5">Identified Intent:</span>
            <code id="nlpIntent" class="text-purple-300 font-mono text-[11px] bg-slate-950 px-2 py-1 rounded block"></code>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px] mb-0.5">NER Tags:</span>
            <div id="nlpEntities" class="flex flex-wrap gap-1"></div>
          </div>
          <div>
            <span class="text-slate-400 block text-[11px] mb-0.5">Generated SQL:</span>
            <code id="nlpSql" class="text-emerald-400 font-mono text-[10px] bg-slate-950 p-2 rounded block break-all"></code>
          </div>
          <div class="bg-slate-950 p-3 rounded-xl border border-slate-800">
            <span class="text-slate-400 text-[10px] uppercase font-bold block mb-1">Answer:</span>
            <p id="nlpAns" class="text-white text-xs"></p>
          </div>
        </div>
      </div>

    </main>

    <!-- Side Navigation Drawer -->
    <div id="drawerOverlay" onclick="toggleDrawer()" class="fixed inset-0 bg-slate-950/70 z-40 hidden"></div>
    <div id="sideDrawer" class="fixed top-0 bottom-0 left-0 w-72 bg-[#0c1626] text-slate-100 z-50 p-6 flex flex-col justify-between transform -translate-x-full transition-transform duration-300 ease-in-out border-r border-slate-800">
      <div class="space-y-6">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center font-bold text-white shadow">BIZ</div>
          <div>
            <h3 class="font-bold text-base leading-tight">BizCore NLP</h3>
            <p class="text-[11px] text-slate-400">{{ user.designation }}</p>
          </div>
        </div>

        <nav class="space-y-1 text-sm font-medium">
          <button onclick="switchTab('pos')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl bg-teal-600/20 text-teal-400">🛒 POS Terminal</button>
          
          {% if user.role == 'admin' %}
          <button onclick="switchTab('employees')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">👥 Staff & Posts</button>
          <button onclick="switchTab('suppliers')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">🚚 Suppliers</button>
          <button onclick="switchTab('purchases')" class="drawer-btn w-full text-left px-3 py-2.5 rounded-xl hover:bg-slate-800 text-slate-300">📥 Inward Purchases</button>
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
        <a href="/logout" class="text-xs text-rose-400 font-bold hover:underline block">Sign out</a>
      </div>
    </div>

    <!-- ==================================================== -->
    <!-- MODALS: ADMIN ACTIONS (Staff, Product, Supplier, etc)-->
    <!-- ==================================================== -->

    <!-- 1. Add Department Modal -->
    <div id="addDeptModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-4">
        <h3 class="font-bold text-sm text-white">Create New Department</h3>
        <input type="text" id="newDeptName" placeholder="Department Name (e.g. Quality Control)" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="flex gap-2">
          <button onclick="closeModal('addDeptModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewDept()" class="w-1/2 py-2 bg-teal-600 text-white text-xs font-bold rounded-xl">Create</button>
        </div>
      </div>
    </div>

    <!-- 2. Add Staff Modal with Custom Post & Department -->
    <div id="addStaffModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 max-h-[90vh] overflow-y-auto">
        <h3 class="font-bold text-sm text-white">Create Staff Member</h3>
        <input type="text" id="staffName" placeholder="Full Name" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="email" id="staffEmail" placeholder="Login Email" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="password" id="staffPass" placeholder="Login Password" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        
        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Select Department OR Add New:</label>
          <select id="staffDeptSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white mb-1.5"></select>
          <input type="text" id="staffCustomDept" placeholder="+ Type custom department if not in list" class="w-full text-xs p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300">
        </div>

        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Assign Post / Designation:</label>
          <select id="staffPostSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white mb-1.5">
            <option value="Store Manager">Store Manager</option>
            <option value="Assistant Manager">Assistant Manager</option>
            <option value="Floor Supervisor">Floor Supervisor</option>
            <option value="Senior Cashier">Senior Cashier</option>
            <option value="POS Cashier">POS Cashier</option>
            <option value="Inventory Controller">Inventory Controller</option>
            <option value="Custom">-- Enter Custom Post Below --</option>
          </select>
          <input type="text" id="staffCustomPost" placeholder="+ Type custom post (e.g. Logistics Lead)" class="w-full text-xs p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300">
        </div>

        <div class="flex gap-2 pt-2">
          <button onclick="closeModal('addStaffModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewStaff()" class="w-1/2 py-2 bg-purple-600 hover:bg-purple-500 font-bold text-white text-xs rounded-xl">Save & Grant Access</button>
        </div>
      </div>
    </div>

    <!-- 3. Add Product Modal -->
    <div id="addProductModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3">
        <h3 class="font-bold text-sm text-white">Register New Product</h3>
        <input type="text" id="pSku" placeholder="SKU Barcode (e.g. ELEC-901)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono">
        <input type="text" id="pName" placeholder="Product Name" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="pCat" placeholder="Category (e.g. Audio, Displays)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="grid grid-cols-2 gap-2">
          <input type="number" step="0.01" id="pCost" placeholder="Cost Price ($)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <input type="number" step="0.01" id="pPrice" placeholder="Selling Price ($)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        </div>
        <input type="number" id="pStock" placeholder="Initial Inventory Stock" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="flex gap-2 pt-2">
          <button onclick="closeModal('addProductModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewProduct()" class="w-1/2 py-2 bg-teal-600 font-bold text-white text-xs rounded-xl">Save Item</button>
        </div>
      </div>
    </div>

    <!-- 4. Add Supplier Modal -->
    <div id="addSupplierModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3">
        <h3 class="font-bold text-sm text-white">Register New Supplier</h3>
        <input type="text" id="sName" placeholder="Supplier / Company Name" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="sContact" placeholder="Contact Person" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="sPhone" placeholder="Phone Number" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="email" id="sEmail" placeholder="Email" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <textarea id="sAddress" placeholder="Address" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white rows-2"></textarea>
        <div class="flex gap-2 pt-2">
          <button onclick="closeModal('addSupplierModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewSupplier()" class="w-1/2 py-2 bg-teal-600 font-bold text-white text-xs rounded-xl">Save Supplier</button>
        </div>
      </div>
    </div>

    <!-- 5. Inward Purchase (Stock Received) Modal -->
    <div id="addPurchaseModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 max-h-[90vh] overflow-y-auto">
        <h3 class="font-bold text-sm text-white">Inward Shipment / Purchase</h3>
        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Select Supplier:</label>
          <select id="purSupplierSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white"></select>
        </div>
        <input type="text" id="purInvoiceRef" placeholder="Supplier Bill / Invoice Ref #" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="date" id="purDate" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">

        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Product Received:</label>
          <select id="purProductSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white"></select>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <input type="number" id="purQty" placeholder="Quantity Inward" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <input type="number" step="0.01" id="purUnitCost" placeholder="Unit Cost Price ($)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        </div>
        <div class="flex gap-2 pt-2">
          <button onclick="closeModal('addPurchaseModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button onclick="submitNewPurchase()" class="w-1/2 py-2 bg-emerald-600 font-bold text-white text-xs rounded-xl">Record & Add Stock</button>
        </div>
      </div>
    </div>

  </div>

  <script>
    let appData = {};
    let cart = [];
    let selectedLineIndex = -1;
    let selectedTenderMode = 'Cash';
    let discountPercent = 0;
    let heldOrders = [];

    function toggleDrawer() {
      document.getElementById('sideDrawer').classList.toggle('-translate-x-full');
      document.getElementById('drawerOverlay').classList.toggle('hidden');
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      const t = document.getElementById('tab-' + tabId);
      if (t) t.classList.remove('hidden');

      const titleMap = {
        'pos': 'POS Terminal',
        'employees': 'Staff & Posts',
        'products': 'Product Catalog',
        'suppliers': 'Suppliers Directory',
        'purchases': 'Inward Purchases',
        'inventory': 'Inventory Monitor',
        'sales': 'Sales Invoices Log',
        'nlp': 'NLP Copilot'
      };
      document.getElementById('pageTitle').innerText = titleMap[tabId] || 'Dashboard';
      toggleDrawer();
    }

    function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
    function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

    // ==========================================
    // COMMERCIAL POS ENGINE
    // ==========================================
    function renderCategoryTabs() {
      const cats = ['ALL', ...new Set(appData.products.map(p => p.category))];
      const box = document.getElementById('posCategoryTabs');
      box.innerHTML = cats.map(c => `
        <button onclick="filterPosCategory('${c}')" class="px-3 py-1.5 rounded-xl ${c === 'ALL' ? 'bg-teal-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'} font-bold whitespace-nowrap">
          ${c}
        </button>
      `).join('');
    }

    function filterPosCategory(cat) {
      const items = cat === 'ALL' ? appData.products : appData.products.filter(p => p.category === cat);
      renderPOSGrid(items);
    }

    function renderPOSGrid(items) {
      const grid = document.getElementById('posGridItems');
      grid.innerHTML = items.map(p => `
        <div onclick="addPosItem(${p.product_id})" class="bg-slate-900 p-2 rounded-xl border border-slate-800 hover:border-teal-500 cursor-pointer flex flex-col justify-between select-none active:scale-95 transition">
          <div>
            <div class="font-bold text-[11px] text-white leading-tight truncate">${p.product_name}</div>
            <div class="text-[9px] text-slate-500 font-mono">${p.sku}</div>
          </div>
          <div class="flex items-center justify-between mt-1 pt-1 border-t border-slate-800/80">
            <span class="font-bold text-xs text-teal-400">$${p.price.toFixed(2)}</span>
            <span class="text-[9px] px-1 rounded ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-slate-400'}">${p.stock}</span>
          </div>
        </div>
      `).join('');
    }

    function addPosItem(productId) {
      const prod = appData.products.find(p => p.product_id === productId);
      if (!prod || prod.stock <= 0) return alert('Out of stock!');

      const exist = cart.find(i => i.product_id === productId);
      if (exist) {
        if (exist.qty < prod.stock) exist.qty += 1;
        else alert('No more available in stock!');
      } else {
        cart.push({ product_id: prod.product_id, sku: prod.sku, name: prod.product_name, price: prod.price, qty: 1 });
      }
      selectedLineIndex = cart.length - 1;
      renderPOSCart();
    }

    function searchAndAddSku() {
      const val = document.getElementById('posSkuInput').value.trim().toLowerCase();
      if (!val) return;
      const found = appData.products.find(p => p.sku.toLowerCase() === val || p.product_name.toLowerCase().includes(val));
      if (found) {
        addPosItem(found.product_id);
        document.getElementById('posSkuInput').value = '';
      } else {
        alert('No product found with SKU/Name: ' + val);
      }
    }

    function selectOrderLine(idx) {
      selectedLineIndex = idx;
      renderPOSCart();
    }

    function renderPOSCart() {
      const box = document.getElementById('posOrderLines');
      if (cart.length === 0) {
        box.innerHTML = '<div class="py-8 text-center text-slate-500 text-xs">No items rung up yet</div>';
        selectedLineIndex = -1;
      } else {
        box.innerHTML = cart.map((it, idx) => `
          <div onclick="selectOrderLine(${idx})" class="px-3 py-2 grid grid-cols-12 cursor-pointer select-none ${selectedLineIndex === idx ? 'bg-teal-950/60 border-l-2 border-teal-400' : 'hover:bg-slate-800/40'}">
            <div class="col-span-5 font-semibold text-white truncate">${it.name}</div>
            <div class="col-span-2 text-center text-teal-300 font-bold font-mono">${it.qty}</div>
            <div class="col-span-2 text-right text-slate-400 font-mono">$${it.price.toFixed(2)}</div>
            <div class="col-span-3 text-right font-extrabold text-white font-mono">$${(it.qty * it.price).toFixed(2)}</div>
          </div>
        `).join('');
      }

      // Math calculations
      const rawSubtotal = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const discountVal = (rawSubtotal * (discountPercent / 100));
      const taxable = rawSubtotal - discountVal;
      const taxVal = taxable * 0.05;
      const totalDue = taxable + taxVal;

      document.getElementById('posSubtotal').innerText = `$${rawSubtotal.toFixed(2)}`;
      document.getElementById('posDiscountAmount').innerText = `-$${discountVal.toFixed(2)} (${discountPercent}%)`;
      document.getElementById('posTax').innerText = `$${taxVal.toFixed(2)}`;
      document.getElementById('posBalanceDue').innerText = `$${totalDue.toFixed(2)}`;
      calculateChange(totalDue);
    }

    // Function Bar Options
    function promptChangeQty() {
      if (selectedLineIndex < 0 || !cart[selectedLineIndex]) return alert('Select an item from the order list first');
      const q = prompt('Enter new quantity for ' + cart[selectedLineIndex].name, cart[selectedLineIndex].qty);
      if (q !== null && parseInt(q) > 0) {
        cart[selectedLineIndex].qty = parseInt(q);
        renderPOSCart();
      }
    }

    function promptDiscount() {
      const d = prompt('Enter Discount Percentage (e.g. 5, 10, 15):', discountPercent);
      if (d !== null && !isNaN(d) && d >= 0 && d <= 100) {
        discountPercent = parseFloat(d);
        renderPOSCart();
      }
    }

    function promptCustomPrice() {
      if (selectedLineIndex < 0 || !cart[selectedLineIndex]) return alert('Select an item first');
      const p = prompt('Price Override for ' + cart[selectedLineIndex].name, cart[selectedLineIndex].price);
      if (p !== null && parseFloat(p) >= 0) {
        cart[selectedLineIndex].price = parseFloat(p);
        renderPOSCart();
      }
    }

    function voidSelectedItem() {
      if (selectedLineIndex < 0 || !cart[selectedLineIndex]) return alert('Select an item to void');
      cart.splice(selectedLineIndex, 1);
      selectedLineIndex = cart.length - 1;
      renderPOSCart();
    }

    function voidEntireSale() {
      if (cart.length === 0) return;
      if (confirm('Void entire transaction?')) clearPosAll();
    }

    function holdCurrentOrder() {
      if (cart.length === 0) return alert('No active order to hold');
      heldOrders.push([...cart]);
      alert(`Order put on Hold (#${heldOrders.length}). Ready for next customer.`);
      clearPosAll();
    }

    function retrieveHeldOrder() {
      if (heldOrders.length === 0) return alert('No orders currently on hold');
      cart = heldOrders.pop();
      selectedLineIndex = cart.length - 1;
      renderPOSCart();
      alert('Held order retrieved successfully');
    }

    function clearPosAll() {
      cart = [];
      selectedLineIndex = -1;
      discountPercent = 0;
      renderPOSCart();
    }

    // Tendering & Math
    function setTenderMode(mode) {
      selectedTenderMode = mode;
      document.querySelectorAll('.tender-mode').forEach(b => {
        b.classList.remove('bg-teal-600', 'text-white');
        b.classList.add('bg-slate-800', 'text-slate-300');
      });
      const act = document.getElementById('tnd' + mode);
      if (act) { act.classList.add('bg-teal-600', 'text-white'); act.classList.remove('bg-slate-800', 'text-slate-300'); }
    }

    function tenderExactAmount() {
      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const total = (rawSub - (rawSub * (discountPercent / 100))) * 1.05;
      calculateChange(total, total);
    }

    function tenderPresetCash(amt) {
      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const total = (rawSub - (rawSub * (discountPercent / 100))) * 1.05;
      calculateChange(total, amt);
    }

    let tenderedGiven = 0;
    function calculateChange(totalDue, tendered = null) {
      if (tendered !== null) tenderedGiven = tendered;
      const change = tenderedGiven > totalDue ? tenderedGiven - totalDue : 0.00;
      document.getElementById('posChangeDue').innerText = `$${change.toFixed(2)}`;
    }

    async function executePOSCheckout() {
      if (cart.length === 0) return alert('No items in transaction!');
      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const discount = rawSub * (discountPercent / 100);
      const tax = (rawSub - discount) * 0.05;
      const total = (rawSub - discount) + tax;
      const change = tenderedGiven > total ? tenderedGiven - total : 0.00;

      const customer = document.getElementById('posCustomerSelect').value;

      const res = await fetch('/api/pos-checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          cart: cart,
          subtotal: rawSub,
          discount: discount,
          tax: tax,
          total: total,
          tendered: tenderedGiven || total,
          change_due: change,
          payment_method: selectedTenderMode,
          customer_name: customer,
          status: 'completed'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert(`========== RECEIPT PRINTED ==========\\nInvoice: ${data.invoice_no}\\nCustomer: ${customer}\\nTotal Amount: $${total.toFixed(2)}\\nPaid via: ${selectedTenderMode} ($${(tenderedGiven || total).toFixed(2)})\\nChange: $${change.toFixed(2)}\\n======================================`);
        clearPosAll();
        loadAllMasterData();
      }
    }

    // ==========================================
    // ADMIN FORMS: DEPT, STAFF, PRODUCT, PURCHASES
    // ==========================================
    async function submitNewDept() {
      const name = document.getElementById('newDeptName').value.trim();
      if (!name) return;
      await fetch('/api/add-department', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ dept_name: name })
      });
      closeModal('addDeptModal');
      loadAllMasterData();
    }

    async function submitNewStaff() {
      const name = document.getElementById('staffName').value.trim();
      const email = document.getElementById('staffEmail').value.trim();
      const pass = document.getElementById('staffPass').value.trim();
      const deptSelect = document.getElementById('staffDeptSelect').value;
      const customDept = document.getElementById('staffCustomDept').value.trim();
      const postSelect = document.getElementById('staffPostSelect').value;
      const customPost = document.getElementById('staffCustomPost').value.trim();

      if (!name || !email || !pass) return alert('Fill required fields');

      await fetch('/api/add-staff', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          name: name,
          email: email,
          password: pass,
          dept_id: deptSelect,
          custom_dept: customDept,
          designation: postSelect === 'Custom' ? customPost : postSelect,
          custom_designation: customPost
        })
      });
      closeModal('addStaffModal');
      alert(`Staff ${name} created successfully. They can login with ${email}`);
      loadAllMasterData();
    }

    async function submitNewProduct() {
      const sku = document.getElementById('pSku').value.trim();
      const name = document.getElementById('pName').value.trim();
      const cat = document.getElementById('pCat').value.trim();
      const cost = document.getElementById('pCost').value;
      const price = document.getElementById('pPrice').value;
      const stock = document.getElementById('pStock').value;

      if (!sku || !name || !price) return alert('SKU, Name and Price are mandatory');

      await fetch('/api/add-product', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sku: sku, product_name: name, category: cat, cost_price: cost, price: price, stock: stock })
      });
      closeModal('addProductModal');
      loadAllMasterData();
    }

    async function submitNewSupplier() {
      const name = document.getElementById('sName').value.trim();
      const person = document.getElementById('sContact').value.trim();
      const phone = document.getElementById('sPhone').value.trim();
      const email = document.getElementById('sEmail').value.trim();
      const addr = document.getElementById('sAddress').value.trim();
      if (!name) return alert('Supplier name required');

      await fetch('/api/add-supplier', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ supplier_name: name, contact_person: person, phone: phone, email: email, address: addr })
      });
      closeModal('addSupplierModal');
      loadAllMasterData();
    }

    async function submitNewPurchase() {
      const supId = document.getElementById('purSupplierSelect').value;
      const ref = document.getElementById('purInvoiceRef').value.trim();
      const date = document.getElementById('purDate').value || new Date().toISOString().slice(0, 10);
      const prodId = document.getElementById('purProductSelect').value;
      const qty = parseInt(document.getElementById('purQty').value || 0);
      const cost = parseFloat(document.getElementById('purUnitCost').value || 0);

      if (!supId || !prodId || qty <= 0) return alert('Select Supplier, Product and valid Quantity');

      const total = qty * cost;
      await fetch('/api/add-purchase', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          supplier_id: supId,
          invoice_ref: ref,
          purchase_date: date,
          total_amount: total,
          items: [{ product_id: prodId, quantity: qty, unit_cost: cost }]
        })
      });
      closeModal('addPurchaseModal');
      alert(`Inward Shipment recorded! ${qty} units added to inventory.`);
      loadAllMasterData();
    }

    // ==========================================
    // NLP EXECUTION
    // ==========================================
    function triggerPrompt(txt) {
      document.getElementById('nlpQueryInput').value = txt;
      runNLP();
    }

    async function runNLP() {
      const q = document.getElementById('nlpQueryInput').value.trim();
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

      document.getElementById('nlpConf').innerText = `Confidence: ${nlp.confidence}`;
      document.getElementById('nlpIntent').innerText = nlp.intent;
      document.getElementById('nlpSql').innerText = nlp.sql;
      document.getElementById('nlpAns').innerText = nlp.answer;

      const entBox = document.getElementById('nlpEntities');
      if (nlp.entities && nlp.entities.length > 0) {
        entBox.innerHTML = nlp.entities.map(e => `
          <span class="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[10px]">
            [${e.type} = "${e.value}"]
          </span>
        `).join('');
      } else {
        entBox.innerHTML = '<span class="text-slate-500 italic">None</span>';
      }
    }

    // ==========================================
    // DATA BINDING
    // ==========================================
    async function loadAllMasterData() {
      const res = await fetch('/api/master-data');
      appData = await res.json();

      // Category Tabs & POS Grid
      renderCategoryTabs();
      renderPOSGrid(appData.products);

      // Populate Dropdowns
      const deptDrop = document.getElementById('staffDeptSelect');
      if (deptDrop) {
        deptDrop.innerHTML = appData.departments.map(d => `<option value="${d.dept_id}">${d.dept_name}</option>`).join('');
      }

      const supDrop = document.getElementById('purSupplierSelect');
      if (supDrop) {
        supDrop.innerHTML = appData.suppliers.map(s => `<option value="${s.supplier_id}">${s.supplier_name}</option>`).join('');
      }

      const prodDrop = document.getElementById('purProductSelect');
      if (prodDrop) {
        prodDrop.innerHTML = appData.products.map(p => `<option value="${p.product_id}">${p.product_name} (${p.sku})</option>`).join('');
      }

      const custDrop = document.getElementById('posCustomerSelect');
      if (custDrop) {
        custDrop.innerHTML = appData.customers.map(c => `<option value="${c.name}">${c.name} (${c.phone})</option>`).join('');
      }

      // Render Staff
      const empBox = document.getElementById('employeesList');
      if (empBox) {
        empBox.innerHTML = appData.employees.map(e => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${e.name}</div>
              <div class="text-[11px] text-purple-400 font-semibold">${e.designation} · <span class="text-slate-400">${e.dept_name || 'General'}</span></div>
              <div class="text-[10px] text-slate-500 font-mono">${e.email}</div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.role === 'admin' ? 'bg-purple-500/20 text-purple-300' : 'bg-teal-500/20 text-teal-300'} capitalize">${e.role}</span>
          </div>
        `).join('');
      }

      // Render Products Master
      const prodBox = document.getElementById('productsMasterList');
      if (prodBox) {
        prodBox.innerHTML = appData.products.map(p => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${p.product_name}</div>
              <div class="text-[11px] text-slate-400">SKU: <span class="font-mono text-teal-300">${p.sku}</span> · Cost: $${p.cost_price.toFixed(2)} · Price: $${p.price.toFixed(2)}</div>
            </div>
            <span class="font-bold px-2.5 py-1 rounded-xl text-xs ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-800 text-teal-400'}">${p.stock} in stock</span>
          </div>
        `).join('');
      }

      // Render Suppliers
      const supBox = document.getElementById('suppliersMasterList');
      if (supBox) {
        supBox.innerHTML = appData.suppliers.map(s => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 text-xs space-y-1">
            <div class="font-bold text-white text-sm">${s.supplier_name}</div>
            <div class="text-[11px] text-slate-400">Contact: ${s.contact_person || 'N/A'} · ${s.phone || 'N/A'}</div>
            <div class="text-[10px] text-slate-500">${s.email || ''} · ${s.address || ''}</div>
          </div>
        `).join('');
      }

      // Render Purchases
      const purBox = document.getElementById('purchasesMasterList');
      if (purBox) {
        purBox.innerHTML = appData.purchases.map(pr => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${pr.supplier_name || 'Supplier Shipment'}</div>
              <div class="text-[11px] text-slate-400">Ref: ${pr.invoice_ref} · ${pr.purchase_date}</div>
            </div>
            <span class="font-extrabold text-emerald-400 text-sm">$${pr.total_amount.toFixed(2)}</span>
          </div>
        `).join('');
      }

      // Render Inventory
      const invBox = document.getElementById('inventoryAlertList');
      if (invBox) {
        invBox.innerHTML = appData.products.map(p => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div class="font-semibold text-white">${p.product_name} (${p.category})</div>
            <span class="font-bold text-xs ${p.stock <= 4 ? 'text-rose-400 font-extrabold' : p.stock < 10 ? 'text-amber-400' : 'text-teal-400'}">${p.stock} units</span>
          </div>
        `).join('');
      }

      // Render Sales Log
      const slBox = document.getElementById('allSalesList');
      if (slBox) {
        slBox.innerHTML = appData.sales.map(s => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${s.invoice_no}</div>
              <div class="text-[11px] text-slate-400">${s.sale_date} · Cashier: ${s.cashier_name} · ${s.customer_name}</div>
            </div>
            <div class="text-right">
              <div class="font-extrabold text-teal-400">$${s.total_amount.toFixed(2)}</div>
              <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">${s.payment_method}</span>
            </div>
          </div>
        `).join('');
      }
    }

    document.addEventListener('DOMContentLoaded', loadAllMasterData);
  </script>
</body>
</html>
"""

with open("templates/dashboard.html", "w") as f:
    f.write(html_code)

print("\nSUCCESS: All enterprise commerce features installed cleanly!")
