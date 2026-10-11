import os
import pymysql

# ==========================================================
# 1. DATABASE SCHEMA MIGRATION: ADD ALL MISSING COLUMNS
# ==========================================================
conn = pymysql.connect(
    host="localhost",
    user="biz_user",
    password="biz_pass123",
    database="business_management"
)
cursor = conn.cursor()

# Ensure default departments exist
cursor.execute("CREATE TABLE IF NOT EXISTS departments (dept_id INT AUTO_INCREMENT PRIMARY KEY, dept_name VARCHAR(100) NOT NULL);")
cursor.execute("INSERT IGNORE INTO departments (dept_id, dept_name) VALUES (1, 'General Operations'), (2, 'Sales & Counter'), (3, 'Store Operations');")

# Fix Employees table columns
cursor.execute("CREATE TABLE IF NOT EXISTS employees (employee_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, designation VARCHAR(100), dept_id INT);")
for col in ["user_id INT"]:
    try: cursor.execute(f"ALTER TABLE employees ADD COLUMN {col};")
    except Exception: pass

# Fix Suppliers table columns
cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id INT AUTO_INCREMENT PRIMARY KEY, supplier_name VARCHAR(150) NOT NULL);")
for col in ["contact_person VARCHAR(100)", "phone VARCHAR(20)", "email VARCHAR(100)", "address TEXT"]:
    try: cursor.execute(f"ALTER TABLE suppliers ADD COLUMN {col};")
    except Exception: pass

# Fix Purchases table columns
cursor.execute("CREATE TABLE IF NOT EXISTS purchases (purchase_id INT AUTO_INCREMENT PRIMARY KEY, purchase_date DATE NOT NULL, total_amount DECIMAL(10, 2) NOT NULL);")
for col in ["supplier_id INT", "invoice_ref VARCHAR(100)", "notes VARCHAR(255)", "status VARCHAR(50) DEFAULT 'Received'"]:
    try: cursor.execute(f"ALTER TABLE purchases ADD COLUMN {col};")
    except Exception: pass

# Fix Products table columns
cursor.execute("CREATE TABLE IF NOT EXISTS products (product_id INT AUTO_INCREMENT PRIMARY KEY, product_name VARCHAR(150) NOT NULL, price DECIMAL(10, 2) NOT NULL, stock INT DEFAULT 0);")
for col in ["sku VARCHAR(50)", "category VARCHAR(100) DEFAULT 'General'", "cost_price DECIMAL(10, 2) DEFAULT 0.00"]:
    try: cursor.execute(f"ALTER TABLE products ADD COLUMN {col};")
    except Exception: pass

# Fix Users table columns
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, password VARCHAR(100) NOT NULL, role ENUM('admin', 'employee') NOT NULL);")
try: cursor.execute("ALTER TABLE users ADD COLUMN designation VARCHAR(100) DEFAULT 'Staff';")
except Exception: pass

# Fix Sales table columns
cursor.execute("CREATE TABLE IF NOT EXISTS sales (sale_id INT AUTO_INCREMENT PRIMARY KEY, invoice_no VARCHAR(50) NOT NULL, sale_date DATE NOT NULL, total_amount DECIMAL(10, 2) NOT NULL);")
for col in ["subtotal DECIMAL(10, 2) DEFAULT 0.00", "discount DECIMAL(10, 2) DEFAULT 0.00", "tax DECIMAL(10, 2) DEFAULT 0.00", "change_due DECIMAL(10, 2) DEFAULT 0.00", "customer_name VARCHAR(100) DEFAULT 'Walk-in Customer'", "cashier_name VARCHAR(100) DEFAULT 'Staff'", "payment_method VARCHAR(50) DEFAULT 'Cash'", "payment_breakdown TEXT"]:
    try: cursor.execute(f"ALTER TABLE sales ADD COLUMN {col};")
    except Exception: pass

conn.commit()
conn.close()
print("Database schema successfully aligned!")

# ==========================================================
# 2. WRITE RESILIENT app.py WITH DETAILED ERROR REPORTING
# ==========================================================
app_code = """from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pymysql.cursors
from nlp_engine.parser import NLPQueryParser

app = Flask(__name__)
app.secret_key = "bizcore_bulletproof_secret_key"

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

@app.route('/api/master-data')
def get_master_data():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products ORDER BY product_id DESC")
            products = cursor.fetchall()
            for p in products:
                p['price'] = float(p.get('price') or 0.0)
                p['cost_price'] = float(p.get('cost_price') or 0.0)
                p['sku'] = p.get('sku') or f"SKU-{p['product_id']}"

            cursor.execute("SELECT * FROM products WHERE stock < 10 ORDER BY stock ASC")
            low_stock = cursor.fetchall()

            cursor.execute("SELECT * FROM sales ORDER BY sale_id DESC")
            sales = cursor.fetchall()
            for s in sales:
                s['sale_date'] = s['sale_date'].strftime('%Y-%m-%d')
                s['total_amount'] = float(s['total_amount'])

            cursor.execute("SELECT * FROM customers ORDER BY name ASC")
            customers = cursor.fetchall()

            cursor.execute(\"\"\"
                SELECT e.employee_id, e.name, e.email, e.designation, IFNULL(d.dept_name, 'General Operations') AS dept_name, IFNULL(u.role, 'employee') AS role
                FROM employees e
                LEFT JOIN departments d ON e.dept_id = d.dept_id
                LEFT JOIN users u ON e.user_id = u.user_id
                ORDER BY e.employee_id DESC
            \"\"\")
            employees = cursor.fetchall()

            cursor.execute("SELECT * FROM departments ORDER BY dept_name ASC")
            departments = cursor.fetchall()

            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
            suppliers = cursor.fetchall()

            cursor.execute(\"\"\"
                SELECT p.*, IFNULL(s.supplier_name, 'Direct Shipment') AS supplier_name 
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

# 1. ADD DEPARTMENT
@app.route('/api/add-department', methods=['POST'])
def add_department():
    d = request.get_json() or {}
    name = (d.get('dept_name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Department name is required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO departments (dept_name) VALUES (%s)", (name,))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 2. CREATE STAFF & CREDENTIALS
@app.route('/api/add-staff', methods=['POST'])
def add_staff():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()

    if not name or not email or not password:
        return jsonify({'status': 'error', 'message': 'Name, email, and password are required'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            dept_id = 1
            if data.get('custom_dept') and data['custom_dept'].strip():
                c_dept = data['custom_dept'].strip()
                cursor.execute("INSERT INTO departments (dept_name) VALUES (%s)", (c_dept,))
                dept_id = cursor.lastrowid
            elif data.get('dept_id') and str(data['dept_id']).strip().isdigit():
                dept_id = int(data['dept_id'])

            post = (data.get('custom_designation') or data.get('designation') or 'Store Staff').strip()

            cursor.execute(\"\"\"
                INSERT INTO users (name, email, password, role, designation)
                VALUES (%s, %s, %s, 'employee', %s)
            \"\"\", (name, email, password, post))
            user_id = cursor.lastrowid

            cursor.execute(\"\"\"
                INSERT INTO employees (name, email, designation, dept_id, user_id)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (name, email, post, dept_id, user_id))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 3. ADD PRODUCT
@app.route('/api/add-product', methods=['POST'])
def add_product():
    d = request.get_json() or {}
    name = (d.get('product_name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Product name is required'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM products")
            cnt = cursor.fetchone()['cnt']
            sku = (d.get('sku') or '').strip() or f"SKU-{100 + cnt + 1}"
            cat = (d.get('category') or 'General').strip()
            cost = float(d.get('cost_price') or 0.0)
            price = float(d.get('price') or 0.0)
            stock = int(d.get('stock') or 0)

            cursor.execute(\"\"\"
                INSERT INTO products (sku, product_name, category, cost_price, price, stock)
                VALUES (%s, %s, %s, %s, %s, %s)
            \"\"\", (sku, name, cat, cost, price, stock))
            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 4. ADD SUPPLIER
@app.route('/api/add-supplier', methods=['POST'])
def add_supplier():
    d = request.get_json() or {}
    name = (d.get('supplier_name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Supplier company name is required'}), 400

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

# 5. INWARD PURCHASES (STOCK ENTRY)
@app.route('/api/add-purchase', methods=['POST'])
def add_purchase():
    d = request.get_json() or {}
    items = d.get('items', [])
    if not items:
        return jsonify({'status': 'error', 'message': 'No items selected in shipment'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sup_id = int(d['supplier_id']) if str(d.get('supplier_id')).isdigit() else None
            tot = float(d.get('total_amount') or 0.0)

            cursor.execute(\"\"\"
                INSERT INTO purchases (supplier_id, invoice_ref, purchase_date, total_amount, notes)
                VALUES (%s, %s, %s, %s, %s)
            \"\"\", (sup_id, d.get('invoice_ref', 'INW-REF'), d.get('purchase_date'), tot, d.get('notes', 'Inward Stock')))

            for it in items:
                cursor.execute(\"\"\"
                    UPDATE products 
                    SET stock = stock + %s, cost_price = %s 
                    WHERE product_id = %s
                \"\"\", (int(it['quantity']), float(it['unit_cost']), int(it['product_id'])))

            conn.commit()
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

# 6. POS CHECKOUT
@app.route('/api/pos-checkout', methods=['POST'])
def pos_checkout():
    d = request.get_json() or {}
    cart = d.get('cart', [])
    if not cart:
        return jsonify({'status': 'error', 'message': 'Cart is empty'}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM sales")
            inv_no = f"INV-{5000 + cursor.fetchone()['cnt'] + 1}"

            subtotal = float(d.get('subtotal', 0))
            discount = float(d.get('discount', 0))
            tax = float(d.get('tax', 0))
            total = float(d.get('total', 0))
            change = float(d.get('change_due', 0))
            customer = d.get('customer_name', 'Walk-in Customer')
            cashier = session['user']['name']
            method_str = d.get('payment_summary', 'Cash')
            breakdown = d.get('payment_breakdown', method_str)

            cursor.execute(\"\"\"
                INSERT INTO sales (invoice_no, sale_date, customer_name, subtotal, discount, tax, total_amount, change_due, payment_method, payment_breakdown, cashier_name)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            \"\"\", (inv_no, customer, subtotal, discount, tax, total, change, method_str, breakdown, cashier))

            for it in cart:
                cursor.execute(\"\"\"
                    UPDATE products SET stock = stock - %s WHERE product_id = %s
                \"\"\", (int(it['qty']), it['product_id']))

            conn.commit()
            return jsonify({'status': 'success', 'invoice_no': inv_no})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
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

# ==========================================================
# 3. WRITE THE COMPLETE TEMPLATE (templates/dashboard.html)
# ==========================================================
html_code = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BizCore NLP - Enterprise POS & Management</title>
  <link rel="manifest" href="/static/manifest.json">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-[#080e1a] text-slate-100 min-h-screen font-sans flex flex-col items-center">

  <div class="w-full max-w-lg bg-[#111c2e] min-h-screen shadow-2xl relative pb-12 flex flex-col border-x border-slate-800">
    <header class="px-5 py-4 flex items-center justify-between border-b border-slate-800 bg-[#111c2e] sticky top-0 z-40">
      <div class="flex items-center space-x-3">
        <button onclick="toggleDrawer()" class="p-2 rounded-2xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
        <div>
          <h1 id="pageTitle" class="text-base font-extrabold text-white leading-tight">POS Terminal</h1>
          <p class="text-[11px] text-teal-400 font-semibold">{{ user.designation }}</p>
        </div>
      </div>
      <span class="px-3 py-1 rounded-full text-[10px] font-bold {% if user.role == 'admin' %}bg-purple-500/20 text-purple-300 border border-purple-500/30{% else %}bg-teal-500/20 text-teal-300 border border-teal-500/30{% endif %} capitalize">
        {{ user.role }}
      </span>
    </header>

    <main class="p-3.5 space-y-4 flex-1">

      <!-- SCREEN 1: POS TERMINAL -->
      <div id="tab-pos" class="tab-pane space-y-3">
        <div class="bg-slate-900/90 rounded-2xl p-3 border border-slate-800 space-y-2">
          <div class="flex gap-2">
            <input type="text" id="posSkuInput" onkeydown="if(event.key==='Enter') searchAndAddSku()" placeholder="🔍 Scan barcode or search SKU/Item..." class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500 font-mono">
            <button onclick="searchAndAddSku()" class="px-4 py-2 bg-gradient-to-r from-teal-600 to-teal-500 text-white rounded-xl text-xs font-bold shadow">Pick</button>
          </div>
          <div class="flex items-center justify-between gap-2 pt-1">
            <div class="flex items-center gap-1.5 flex-1">
              <span class="text-[11px] text-slate-400">Sort:</span>
              <select id="posSortSelect" onchange="renderFilteredPOS()" class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-[11px] text-slate-200">
                <option value="name-asc">Name (A → Z)</option>
                <option value="name-desc">Name (Z → A)</option>
                <option value="price-asc">Price (Low → High)</option>
                <option value="price-desc">Price (High → Low)</option>
                <option value="stock-asc">Stock (Low first ⚠️)</option>
                <option value="stock-desc">Stock (High → Low)</option>
              </select>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] text-slate-400">Cust:</span>
              <select id="posCustomerSelect" class="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-[11px] text-slate-200">
                <option value="Walk-in Customer">Walk-in Customer</option>
              </select>
            </div>
          </div>
        </div>

        <div id="posCategoryTabs" class="flex gap-1.5 overflow-x-auto pb-1 text-[11px] scrollbar-none"></div>
        <div id="posGridItems" class="grid grid-cols-3 gap-2 max-h-44 overflow-y-auto pr-1"></div>

        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow">
          <div class="bg-slate-800/90 px-3 py-2 grid grid-cols-12 text-[10px] font-extrabold text-slate-300 uppercase tracking-wider">
            <span class="col-span-5">Item</span>
            <span class="col-span-2 text-center">Qty</span>
            <span class="col-span-2 text-right">Price</span>
            <span class="col-span-3 text-right">Total</span>
          </div>
          <div id="posOrderLines" class="divide-y divide-slate-800/80 max-h-40 overflow-y-auto text-xs min-h-[90px]">
            <div class="py-8 text-center text-slate-500 text-xs">No items rung up yet</div>
          </div>
        </div>

        <!-- POS BUTTONS -->
        <div class="grid grid-cols-4 gap-2">
          <button onclick="promptChangeQty()" class="bg-gradient-to-br from-indigo-950 to-slate-900 border border-indigo-500/40 hover:border-indigo-400 active:scale-95 text-indigo-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">🔢</span><span>Qty</span>
          </button>
          <button onclick="promptDiscount()" class="bg-gradient-to-br from-emerald-950 to-slate-900 border border-emerald-500/40 hover:border-emerald-400 active:scale-95 text-emerald-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">🏷️</span><span>Discount</span>
          </button>
          <button onclick="voidSelectedItem()" class="bg-gradient-to-br from-amber-950 to-slate-900 border border-amber-500/40 hover:border-amber-400 active:scale-95 text-amber-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">⚠️</span><span>Void Item</span>
          </button>
          <button onclick="voidEntireSale()" class="bg-gradient-to-br from-rose-950 to-slate-900 border border-rose-500/40 hover:border-rose-400 active:scale-95 text-rose-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">🚫</span><span>Void Sale</span>
          </button>
          <button onclick="holdCurrentOrder()" class="bg-gradient-to-br from-purple-950 to-slate-900 border border-purple-500/40 hover:border-purple-400 active:scale-95 text-purple-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">⏸️</span><span>Hold</span>
          </button>
          <button onclick="retrieveHeldOrder()" class="bg-gradient-to-br from-blue-950 to-slate-900 border border-blue-500/40 hover:border-blue-400 active:scale-95 text-blue-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">▶️</span><span>Retrieve</span>
          </button>
          <button onclick="promptCustomPrice()" class="bg-gradient-to-br from-cyan-950 to-slate-900 border border-cyan-500/40 hover:border-cyan-400 active:scale-95 text-cyan-300 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">💲</span><span>Price Ovr</span>
          </button>
          <button onclick="clearPosAll()" class="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-700 hover:border-slate-500 active:scale-95 text-slate-400 py-2.5 px-1 rounded-xl text-xs font-bold flex flex-col items-center justify-center gap-0.5 shadow transition">
            <span class="text-sm">🧹</span><span>Clear</span>
          </button>
        </div>

        <div class="bg-slate-900/90 rounded-2xl p-3 border border-slate-800 space-y-1.5 text-xs">
          <div class="flex justify-between text-slate-400"><span>Sub Total:</span><span id="posSubtotal" class="font-mono text-white">$0.00</span></div>
          <div class="flex justify-between text-slate-400"><span>Discount:</span><span id="posDiscountAmount" class="font-mono text-emerald-400">-$0.00 (0%)</span></div>
          <div class="flex justify-between text-slate-400"><span>Tax (5%):</span><span id="posTax" class="font-mono text-white">$0.00</span></div>
          <div class="flex justify-between text-sm font-extrabold text-teal-400 border-t border-slate-800 pt-1">
            <span>Net Amount Due:</span><span id="posTotalDue" class="font-mono">$0.00</span>
          </div>
        </div>

        <!-- SPLIT PAYMENT SECTION -->
        <div class="bg-gradient-to-br from-slate-900 to-slate-950 rounded-2xl p-3.5 border border-teal-500/30 space-y-3 shadow-lg">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-teal-300 flex items-center gap-1.5">
              <span>💳</span> Payment Tenders & Split Modes
            </span>
            <span id="posSplitStatus" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">Unpaid</span>
          </div>

          <div id="appliedTendersContainer" class="space-y-1.5 text-xs">
            <div class="text-[11px] text-slate-500 italic py-1">No payment tenders added yet.</div>
          </div>

          <div class="flex justify-between items-center text-xs bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <div>
              <span class="text-slate-400 block text-[10px]">Remaining Balance:</span>
              <span id="posRemainingDue" class="font-mono font-extrabold text-amber-400 text-sm">$0.00</span>
            </div>
            <div class="text-right">
              <span class="text-slate-400 block text-[10px]">Change to Customer:</span>
              <span id="posChangeDue" class="font-mono font-extrabold text-emerald-400 text-sm">$0.00</span>
            </div>
          </div>

          <div class="space-y-2 pt-1 border-t border-slate-800">
            <div class="flex gap-2">
              <select id="tenderMethodSelect" class="bg-slate-950 border border-slate-700 text-xs text-white rounded-xl px-2 py-2">
                <option value="Cash">Cash 💵</option>
                <option value="UPI">UPI / QR 📱</option>
                <option value="Card">Card 💳</option>
                <option value="Check">Check 📝</option>
                <option value="Store Credit">Store Credit 🎟️</option>
              </select>
              <input type="number" step="0.01" id="tenderAmountInput" placeholder="Amount ($)" class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500 font-mono">
              <button onclick="addPaymentTender()" class="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold shadow">+ Add</button>
            </div>

            <div class="flex gap-1.5 text-[10px]">
              <button onclick="fillExactRemaining()" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-teal-300 font-bold border border-slate-700">Exact Remaining</button>
              <button onclick="setQuickTender(10)" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">$10</button>
              <button onclick="setQuickTender(20)" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">$20</button>
              <button onclick="setQuickTender(50)" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">$50</button>
              <button onclick="setQuickTender(100)" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700">$100</button>
            </div>
          </div>

          <button onclick="completeSplitCheckout()" id="btnCompleteSale" class="w-full py-3.5 bg-slate-800 font-extrabold text-slate-500 text-xs rounded-2xl shadow transition opacity-50 cursor-not-allowed">
            Complete Transaction & Print Receipt 🖨️
          </button>
        </div>
      </div>

      <!-- SCREEN 2: STAFF & POSTS -->
      <div id="tab-employees" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Staff Directory & Roles</span>
          <div class="flex gap-2">
            <button onclick="openModal('addDeptModal')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-teal-300 rounded-xl text-xs font-semibold border border-slate-700">+ New Dept</button>
            <button onclick="openModal('addStaffModal')" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold shadow">+ Add Staff</button>
          </div>
        </div>
        <div id="employeesList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 3: PRODUCT CATALOG -->
      <div id="tab-products" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center gap-2">
          <select id="catalogSortSelect" onchange="renderProductsMasterList()" class="bg-slate-900 border border-slate-700 text-[11px] rounded-xl px-2.5 py-1.5 text-slate-300">
            <option value="name-asc">Sort: Name (A → Z)</option>
            <option value="name-desc">Sort: Name (Z → A)</option>
            <option value="price-asc">Sort: Price (Low → High)</option>
            <option value="price-desc">Sort: Price (High → Low)</option>
            <option value="stock-asc">Sort: Low Stock First</option>
            <option value="stock-desc">Sort: High Stock First</option>
          </select>
          <button onclick="openModal('addProductModal')" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold shadow">+ Add Product</button>
        </div>
        <div id="productsMasterList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 4: SUPPLIERS DIRECTORY -->
      <div id="tab-suppliers" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Suppliers Directory</span>
          <button onclick="openModal('addSupplierModal')" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl text-xs font-bold shadow">+ Add Supplier</button>
        </div>
        <div id="suppliersMasterList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 5: INWARD PURCHASES -->
      <div id="tab-purchases" class="tab-pane space-y-3 hidden">
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400 font-semibold">Inward Shipments (Restock)</span>
          <button onclick="openModal('addPurchaseModal')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow">+ Inward Stock</button>
        </div>
        <div id="purchasesMasterList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 6: INVENTORY MONITOR -->
      <div id="tab-inventory" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Inventory Stock Levels</div>
        <div id="inventoryAlertList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 7: SALES INVOICES -->
      <div id="tab-sales" class="tab-pane space-y-3 hidden">
        <div class="text-xs text-slate-400 font-semibold">Sales Log</div>
        <div id="allSalesList" class="space-y-2"></div>
      </div>

      <!-- SCREEN 8: NLP COPILOT -->
      <div id="tab-nlp" class="tab-pane space-y-3 hidden">
        <div class="bg-slate-900 rounded-2xl p-4 border border-slate-800 space-y-3">
          <div class="flex items-center space-x-2">
            <span class="p-1 rounded-md bg-teal-500/20 text-teal-400 font-bold text-[10px]">NLP ENGINE</span>
            <span class="text-xs text-slate-400 font-medium">Text-to-SQL Interpreter</span>
          </div>
          <div class="flex gap-2">
            <input id="nlpQueryInput" type="text" placeholder="e.g. Which products have less than 10 items?" class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-teal-500">
            <button onclick="runNLP()" class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white font-bold rounded-xl text-xs">Run</button>
          </div>
        </div>
        <div id="nlpInspectorCard" class="bg-slate-900 rounded-2xl p-4 border border-slate-800 space-y-3 hidden text-xs">
          <div class="font-bold text-teal-400 flex items-center justify-between border-b border-slate-800 pb-2">
            <span>Query Inspection</span>
            <span id="nlpConf" class="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded-full"></span>
          </div>
          <div><code id="nlpIntent" class="text-purple-300 font-mono text-[11px] bg-slate-950 px-2 py-1 rounded block"></code></div>
          <div><code id="nlpSql" class="text-emerald-400 font-mono text-[10px] bg-slate-950 p-2 rounded block break-all"></code></div>
          <div class="bg-slate-950 p-3 rounded-xl border border-slate-800"><p id="nlpAns" class="text-white text-xs"></p></div>
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

    <!-- MODAL 1: ADD DEPARTMENT -->
    <div id="addDeptModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-4 shadow-2xl">
        <h3 class="font-bold text-sm text-white">Create New Department</h3>
        <input type="text" id="newDeptName" placeholder="Department Name (e.g. Accounts)" class="w-full text-xs p-3 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="flex gap-2">
          <button type="button" onclick="closeModal('addDeptModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button type="button" onclick="submitNewDept()" class="w-1/2 py-2 bg-teal-600 text-white text-xs font-bold rounded-xl">Create</button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: ADD STAFF -->
    <div id="addStaffModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 max-h-[90vh] overflow-y-auto shadow-2xl">
        <h3 class="font-bold text-sm text-white">Create Staff Member & Post</h3>
        <input type="text" id="staffName" placeholder="Full Name *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="email" id="staffEmail" placeholder="Login Email *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="password" id="staffPass" placeholder="Login Password *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        
        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Department:</label>
          <select id="staffDeptSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white mb-1.5"></select>
          <input type="text" id="staffCustomDept" placeholder="+ Type new department if not in list" class="w-full text-xs p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300">
        </div>

        <div>
          <label class="text-[11px] text-slate-400 block mb-1">Assign Post / Designation:</label>
          <select id="staffPostSelect" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white mb-1.5">
            <option value="Store Manager">Store Manager</option>
            <option value="Floor Supervisor">Floor Supervisor</option>
            <option value="POS Cashier">POS Cashier</option>
            <option value="Inventory Officer">Inventory Officer</option>
            <option value="Custom">-- Type Custom Post Below --</option>
          </select>
          <input type="text" id="staffCustomPost" placeholder="+ Type custom post (e.g. Lead Auditor)" class="w-full text-xs p-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-300">
        </div>

        <div class="flex gap-2 pt-2">
          <button type="button" onclick="closeModal('addStaffModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button type="button" onclick="submitNewStaff()" class="w-1/2 py-2 bg-purple-600 hover:bg-purple-500 font-bold text-white text-xs rounded-xl shadow">Create Staff</button>
        </div>
      </div>
    </div>

    <!-- MODAL 3: ADD PRODUCT -->
    <div id="addProductModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 shadow-2xl">
        <h3 class="font-bold text-sm text-white">Register New Product</h3>
        <input type="text" id="pSku" placeholder="SKU / Barcode (Leave empty to auto-generate)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono">
        <input type="text" id="pName" placeholder="Product Name *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="pCat" placeholder="Category (e.g. Displays, Grocery)" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="grid grid-cols-2 gap-2">
          <input type="number" step="0.01" id="pCost" placeholder="Cost Price ($)" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
          <input type="number" step="0.01" id="pPrice" placeholder="Selling Price ($) *" class="text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        </div>
        <input type="number" id="pStock" placeholder="Initial Inventory Stock" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <div class="flex gap-2 pt-2">
          <button type="button" onclick="closeModal('addProductModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button type="button" onclick="submitNewProduct()" class="w-1/2 py-2 bg-teal-600 hover:bg-teal-500 font-bold text-white text-xs rounded-xl shadow">Save Item</button>
        </div>
      </div>
    </div>

    <!-- MODAL 4: ADD SUPPLIER -->
    <div id="addSupplierModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 shadow-2xl">
        <h3 class="font-bold text-sm text-white">Register New Supplier</h3>
        <input type="text" id="sName" placeholder="Supplier / Company Name *" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="sContact" placeholder="Contact Person" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="text" id="sPhone" placeholder="Phone Number" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <input type="email" id="sEmail" placeholder="Email" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white">
        <textarea id="sAddress" placeholder="Address" class="w-full text-xs p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white" rows="2"></textarea>
        <div class="flex gap-2 pt-2">
          <button type="button" onclick="closeModal('addSupplierModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button type="button" onclick="submitNewSupplier()" class="w-1/2 py-2 bg-teal-600 font-bold text-white text-xs rounded-xl shadow">Save Supplier</button>
        </div>
      </div>
    </div>

    <!-- MODAL 5: INWARD PURCHASE -->
    <div id="addPurchaseModal" class="fixed inset-0 bg-slate-950/70 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-[#141f32] border border-slate-800 rounded-3xl p-5 w-full max-w-sm space-y-3 max-h-[90vh] overflow-y-auto shadow-2xl">
        <h3 class="font-bold text-sm text-white">Inward Shipment / Restock</h3>
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
          <button type="button" onclick="closeModal('addPurchaseModal')" class="w-1/2 py-2 bg-slate-800 text-slate-300 text-xs rounded-xl">Cancel</button>
          <button type="button" onclick="submitNewPurchase()" class="w-1/2 py-2 bg-emerald-600 font-bold text-white text-xs rounded-xl shadow">Record & Restock</button>
        </div>
      </div>
    </div>

    <!-- MODAL 6: THERMAL RECEIPT -->
    <div id="receiptModal" class="fixed inset-0 bg-slate-950/80 z-50 hidden flex items-center justify-center p-4">
      <div class="bg-white text-slate-900 rounded-3xl p-6 w-full max-w-xs space-y-4 font-mono text-xs shadow-2xl">
        <div class="text-center border-b pb-2">
          <h2 class="font-extrabold text-base">BIZCORE STORE</h2>
          <p class="text-[10px] text-slate-500">Official Sales Receipt</p>
          <p id="rcptInv" class="text-[11px] font-bold mt-1 text-slate-700"></p>
        </div>
        <div id="rcptItems" class="space-y-1 text-[11px] border-b pb-2"></div>
        <div class="space-y-1 text-[11px] border-b pb-2">
          <div class="flex justify-between"><span>Subtotal:</span><span id="rcptSub"></span></div>
          <div class="flex justify-between"><span>Discount:</span><span id="rcptDisc"></span></div>
          <div class="flex justify-between"><span>Tax (5%):</span><span id="rcptTax"></span></div>
          <div class="flex justify-between font-extrabold text-sm border-t pt-1"><span>TOTAL:</span><span id="rcptTotal"></span></div>
        </div>
        <div>
          <span class="font-bold text-[10px] uppercase text-slate-500 block mb-1">Tender Breakdown:</span>
          <div id="rcptTenders" class="space-y-0.5 text-[11px]"></div>
          <div class="flex justify-between font-bold text-emerald-700 mt-1 border-t pt-1">
            <span>Change Returned:</span><span id="rcptChange"></span>
          </div>
        </div>
        <button type="button" onclick="closeReceiptAndReset()" class="w-full py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold uppercase tracking-wider">Done & Next Sale</button>
      </div>
    </div>

  </div>

  <script>
    let appData = {};
    let cart = [];
    let selectedLineIndex = -1;
    let discountPercent = 0;
    let appliedTenders = [];
    let heldOrders = [];
    let currentCategory = 'ALL';

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
        'sales': 'Sales Invoices',
        'nlp': 'NLP Copilot'
      };
      document.getElementById('pageTitle').innerText = titleMap[tabId] || 'Dashboard';
      toggleDrawer();
    }

    function openModal(id) { 
      const m = document.getElementById(id);
      if (m) m.classList.remove('hidden');
    }
    function closeModal(id) { 
      const m = document.getElementById(id);
      if (m) m.classList.add('hidden');
    }

    function sortItemsList(items, sortKey) {
      const sorted = [...items];
      if (sortKey === 'name-asc') sorted.sort((a, b) => a.product_name.localeCompare(b.product_name));
      else if (sortKey === 'name-desc') sorted.sort((a, b) => b.product_name.localeCompare(a.product_name));
      else if (sortKey === 'price-asc') sorted.sort((a, b) => a.price - b.price);
      else if (sortKey === 'price-desc') sorted.sort((a, b) => b.price - a.price);
      else if (sortKey === 'stock-asc') sorted.sort((a, b) => a.stock - b.stock);
      else if (sortKey === 'stock-desc') sorted.sort((a, b) => b.stock - a.stock);
      return sorted;
    }

    function renderFilteredPOS() {
      const sortSelect = document.getElementById('posSortSelect');
      const sortVal = sortSelect ? sortSelect.value : 'name-asc';
      let items = (appData.products || []);
      if (currentCategory !== 'ALL') {
        items = items.filter(p => p.category === currentCategory);
      }
      renderPOSGrid(sortItemsList(items, sortVal));
    }

    function renderCategoryTabs() {
      const cats = ['ALL', ...new Set((appData.products || []).map(p => p.category))];
      const box = document.getElementById('posCategoryTabs');
      if (!box) return;
      box.innerHTML = cats.map(c => `
        <button type="button" onclick="setCategoryFilter('${c}')" class="px-3 py-1.5 rounded-xl ${c === currentCategory ? 'bg-teal-600 text-white font-extrabold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'} whitespace-nowrap transition">
          ${c}
        </button>
      `).join('');
    }

    function setCategoryFilter(cat) {
      currentCategory = cat;
      renderCategoryTabs();
      renderFilteredPOS();
    }

    function renderPOSGrid(items) {
      const grid = document.getElementById('posGridItems');
      if (!grid) return;
      if (!items || items.length === 0) {
        grid.innerHTML = '<div class="col-span-3 text-center text-slate-500 text-xs py-4">No products found</div>';
        return;
      }
      grid.innerHTML = items.map(p => `
        <div onclick="addPosItem(${p.product_id})" class="bg-slate-900 p-2.5 rounded-2xl border border-slate-800 hover:border-teal-500 cursor-pointer flex flex-col justify-between active:scale-95 transition shadow-sm">
          <div>
            <div class="font-bold text-[11px] text-white leading-tight truncate">${p.product_name}</div>
            <div class="text-[9px] text-teal-400 font-mono mt-0.5">${p.sku}</div>
          </div>
          <div class="flex items-center justify-between mt-2 pt-1 border-t border-slate-800">
            <span class="font-extrabold text-xs text-white">$${p.price.toFixed(2)}</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300 font-bold' : 'bg-slate-800 text-slate-400'}">${p.stock}</span>
          </div>
        </div>
      `).join('');
    }

    function addPosItem(productId) {
      const prod = (appData.products || []).find(p => p.product_id === productId);
      if (!prod || prod.stock <= 0) return alert('Out of stock!');

      const exist = cart.find(i => i.product_id === productId);
      if (exist) {
        if (exist.qty < prod.stock) exist.qty += 1;
        else alert('No more stock available in inventory!');
      } else {
        cart.push({ product_id: prod.product_id, sku: prod.sku, name: prod.product_name, price: prod.price, qty: 1 });
      }
      selectedLineIndex = cart.length - 1;
      renderPOSCart();
    }

    function searchAndAddSku() {
      const val = document.getElementById('posSkuInput').value.trim().toLowerCase();
      if (!val) return;
      const found = (appData.products || []).find(p => p.sku.toLowerCase() === val || p.product_name.toLowerCase().includes(val));
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
      if (!box) return;
      if (cart.length === 0) {
        box.innerHTML = '<div class="py-8 text-center text-slate-500 text-xs">No items rung up yet</div>';
        selectedLineIndex = -1;
      } else {
        box.innerHTML = cart.map((it, idx) => `
          <div onclick="selectOrderLine(${idx})" class="px-3 py-2 grid grid-cols-12 cursor-pointer select-none ${selectedLineIndex === idx ? 'bg-teal-950/70 border-l-4 border-teal-400' : 'hover:bg-slate-800/40'}">
            <div class="col-span-5 font-semibold text-white truncate">${it.name}</div>
            <div class="col-span-2 text-center text-teal-300 font-bold font-mono">${it.qty}</div>
            <div class="col-span-2 text-right text-slate-400 font-mono">$${it.price.toFixed(2)}</div>
            <div class="col-span-3 text-right font-extrabold text-white font-mono">$${(it.qty * it.price).toFixed(2)}</div>
          </div>
        `).join('');
      }

      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const disc = rawSub * (discountPercent / 100);
      const taxable = rawSub - disc;
      const tax = taxable * 0.05;
      const total = taxable + tax;

      document.getElementById('posSubtotal').innerText = `$${rawSub.toFixed(2)}`;
      document.getElementById('posDiscountAmount').innerText = `-$${disc.toFixed(2)} (${discountPercent}%)`;
      document.getElementById('posTax').innerText = `$${tax.toFixed(2)}`;
      document.getElementById('posTotalDue').innerText = `$${total.toFixed(2)}`;

      updateSplitTendersView(total);
    }

    function promptChangeQty() {
      if (selectedLineIndex < 0 || !cart[selectedLineIndex]) return alert('Select an item from the receipt table first');
      const q = prompt('Enter new quantity for ' + cart[selectedLineIndex].name, cart[selectedLineIndex].qty);
      if (q !== null && parseInt(q) > 0) {
        cart[selectedLineIndex].qty = parseInt(q);
        renderPOSCart();
      }
    }

    function promptDiscount() {
      const d = prompt('Enter Discount Percentage (0 to 100):', discountPercent);
      if (d !== null && !isNaN(d) && d >= 0 && d <= 100) {
        discountPercent = parseFloat(d);
        renderPOSCart();
      }
    }

    function promptCustomPrice() {
      if (selectedLineIndex < 0 || !cart[selectedLineIndex]) return alert('Select an item first');
      const p = prompt('Override price for ' + cart[selectedLineIndex].name, cart[selectedLineIndex].price);
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
      if (cart.length === 0) return alert('No active order to put on hold');
      heldOrders.push({ cart: [...cart], discount: discountPercent });
      alert(`Order held (#${heldOrders.length}). Ready for next customer.`);
      clearPosAll();
    }

    function retrieveHeldOrder() {
      if (heldOrders.length === 0) return alert('No orders currently on hold');
      const held = heldOrders.pop();
      cart = held.cart;
      discountPercent = held.discount;
      selectedLineIndex = cart.length - 1;
      renderPOSCart();
      alert('Held order retrieved successfully');
    }

    function clearPosAll() {
      cart = [];
      selectedLineIndex = -1;
      discountPercent = 0;
      appliedTenders = [];
      renderPOSCart();
    }

    function calculateTotalDue() {
      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const disc = rawSub * (discountPercent / 100);
      return (rawSub - disc) * 1.05;
    }

    function updateSplitTendersView(totalDue = null) {
      if (totalDue === null) totalDue = calculateTotalDue();

      const totalPaid = appliedTenders.reduce((acc, t) => acc + t.amount, 0);
      const remaining = Math.max(0, totalDue - totalPaid);
      const change = Math.max(0, totalPaid - totalDue);

      document.getElementById('posRemainingDue').innerText = `$${remaining.toFixed(2)}`;
      document.getElementById('posChangeDue').innerText = `$${change.toFixed(2)}`;

      const statusBadge = document.getElementById('posSplitStatus');
      const checkoutBtn = document.getElementById('btnCompleteSale');

      if (totalDue > 0 && remaining <= 0.001) {
        statusBadge.innerText = 'Paid in Full ✓';
        statusBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300';
        checkoutBtn.className = 'w-full py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 font-extrabold text-white text-xs rounded-2xl shadow-xl transition cursor-pointer active:scale-95';
        checkoutBtn.removeAttribute('disabled');
      } else {
        statusBadge.innerText = remaining === totalDue ? 'Unpaid' : 'Partially Paid';
        statusBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300';
        checkoutBtn.className = 'w-full py-3.5 bg-slate-800 font-extrabold text-slate-500 text-xs rounded-2xl shadow transition opacity-50 cursor-not-allowed';
        checkoutBtn.setAttribute('disabled', 'true');
      }

      const tenderBox = document.getElementById('appliedTendersContainer');
      if (appliedTenders.length === 0) {
        tenderBox.innerHTML = '<div class="text-[11px] text-slate-500 italic py-1">No payment tenders added yet.</div>';
      } else {
        tenderBox.innerHTML = appliedTenders.map((t, idx) => `
          <div class="flex items-center justify-between bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
            <span class="font-semibold text-slate-200">${t.method}: <span class="font-mono text-teal-400 font-bold">$${t.amount.toFixed(2)}</span></span>
            <button type="button" onclick="removeTender(${idx})" class="text-rose-400 hover:text-rose-300 font-bold text-xs p-1">✕</button>
          </div>
        `).join('');
      }
    }

    function addPaymentTender() {
      const totalDue = calculateTotalDue();
      if (totalDue <= 0) return alert('Add items to order before accepting payment');

      const method = document.getElementById('tenderMethodSelect').value;
      const amtInput = document.getElementById('tenderAmountInput');
      const amt = parseFloat(amtInput.value);

      if (isNaN(amt) || amt <= 0) return alert('Please enter a valid payment amount');

      appliedTenders.push({ method: method, amount: amt });
      amtInput.value = '';
      updateSplitTendersView(totalDue);
    }

    function removeTender(idx) {
      appliedTenders.splice(idx, 1);
      updateSplitTendersView();
    }

    function fillExactRemaining() {
      const totalDue = calculateTotalDue();
      const totalPaid = appliedTenders.reduce((acc, t) => acc + t.amount, 0);
      const remaining = Math.max(0, totalDue - totalPaid);
      document.getElementById('tenderAmountInput').value = remaining.toFixed(2);
    }

    function setQuickTender(val) {
      document.getElementById('tenderAmountInput').value = val.toFixed(2);
    }

    async function completeSplitCheckout() {
      const totalDue = calculateTotalDue();
      const totalPaid = appliedTenders.reduce((acc, t) => acc + t.amount, 0);
      if (totalPaid < totalDue - 0.001) return alert('Payment incomplete! Remaining balance must be $0.00');

      const change = Math.max(0, totalPaid - totalDue);
      const rawSub = cart.reduce((acc, i) => acc + (i.price * i.qty), 0);
      const discount = rawSub * (discountPercent / 100);
      const tax = (rawSub - discount) * 0.05;
      const customer = document.getElementById('posCustomerSelect').value;
      const paymentSummary = appliedTenders.map(t => `${t.method} ($${t.amount.toFixed(2)})`).join(', ');

      try {
        const res = await fetch('/api/pos-checkout', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            cart: cart,
            subtotal: rawSub,
            discount: discount,
            tax: tax,
            total: totalDue,
            change_due: change,
            customer_name: customer,
            payment_summary: paymentSummary,
            payment_breakdown: JSON.stringify(appliedTenders)
          })
        });
        const d = await res.json();
        if (d.status === 'success') {
          showReceiptModal(d.invoice_no, customer, rawSub, discount, tax, totalDue, appliedTenders, change);
          await loadAllMasterData();
        } else {
          alert('Checkout failed: ' + (d.message || 'Unknown error'));
        }
      } catch (err) {
        alert('Network/Server Error: ' + err.message);
      }
    }

    function showReceiptModal(inv, cust, sub, disc, tax, tot, tenders, change) {
      document.getElementById('rcptInv').innerText = `${inv} · ${cust}`;
      document.getElementById('rcptItems').innerHTML = cart.map(i => `
        <div class="flex justify-between">
          <span>${i.name} x${i.qty}</span>
          <span>$${(i.qty * i.price).toFixed(2)}</span>
        </div>
      `).join('');
      document.getElementById('rcptSub').innerText = `$${sub.toFixed(2)}`;
      document.getElementById('rcptDisc').innerText = `-$${disc.toFixed(2)}`;
      document.getElementById('rcptTax').innerText = `$${tax.toFixed(2)}`;
      document.getElementById('rcptTotal').innerText = `$${tot.toFixed(2)}`;

      document.getElementById('rcptTenders').innerHTML = tenders.map(t => `
        <div class="flex justify-between text-slate-700">
          <span>${t.method}:</span>
          <span>$${t.amount.toFixed(2)}</span>
        </div>
      `).join('');

      document.getElementById('rcptChange').innerText = `$${change.toFixed(2)}`;
      openModal('receiptModal');
    }

    function closeReceiptAndReset() {
      closeModal('receiptModal');
      clearPosAll();
    }

    // ==========================================
    // ACTION SUBMISSIONS WITH TRY/CATCH & ALERTS
    // ==========================================
    async function submitNewDept() {
      try {
        const name = document.getElementById('newDeptName').value.trim();
        if (!name) return alert('Department name is required');
        const res = await fetch('/api/add-department', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ dept_name: name })
        });
        const d = await res.json();
        if (d.status === 'success') {
          closeModal('addDeptModal');
          document.getElementById('newDeptName').value = '';
          await loadAllMasterData();
          alert('Department "' + name + '" created successfully!');
        } else {
          alert('Error: ' + (d.message || 'Could not save department'));
        }
      } catch (err) {
        alert('Request failed: ' + err.message);
      }
    }

    async function submitNewStaff() {
      try {
        const name = document.getElementById('staffName').value.trim();
        const email = document.getElementById('staffEmail').value.trim();
        const pass = document.getElementById('staffPass').value.trim();
        const deptSelect = document.getElementById('staffDeptSelect').value;
        const customDept = document.getElementById('staffCustomDept').value.trim();
        const postSelect = document.getElementById('staffPostSelect').value;
        const customPost = document.getElementById('staffCustomPost').value.trim();

        if (!name || !email || !pass) return alert('Name, Email, and Password are required!');

        const res = await fetch('/api/add-staff', {
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
        const d = await res.json();
        if (d.status === 'success') {
          closeModal('addStaffModal');
          document.getElementById('staffName').value = '';
          document.getElementById('staffEmail').value = '';
          document.getElementById('staffPass').value = '';
          document.getElementById('staffCustomDept').value = '';
          document.getElementById('staffCustomPost').value = '';
          await loadAllMasterData();
          alert(`Staff member "${name}" registered successfully!`);
        } else {
          alert('Error creating staff: ' + (d.message || 'Server error'));
        }
      } catch (err) {
        alert('Request failed: ' + err.message);
      }
    }

    async function submitNewProduct() {
      try {
        const sku = document.getElementById('pSku').value.trim();
        const name = document.getElementById('pName').value.trim();
        const cat = document.getElementById('pCat').value.trim();
        const cost = document.getElementById('pCost').value || 0;
        const price = document.getElementById('pPrice').value;
        const stock = document.getElementById('pStock').value || 0;

        if (!name || !price) return alert('Product Name and Selling Price are required!');

        const res = await fetch('/api/add-product', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ sku: sku, product_name: name, category: cat, cost_price: cost, price: price, stock: stock })
        });
        const d = await res.json();
        if (d.status === 'success') {
          closeModal('addProductModal');
          document.getElementById('pSku').value = '';
          document.getElementById('pName').value = '';
          document.getElementById('pCat').value = '';
          document.getElementById('pCost').value = '';
          document.getElementById('pPrice').value = '';
          document.getElementById('pStock').value = '';
          await loadAllMasterData();
          alert(`Product "${name}" added to catalog and POS grid!`);
        } else {
          alert('Error adding product: ' + (d.message || 'Server error'));
        }
      } catch (err) {
        alert('Request failed: ' + err.message);
      }
    }

    async function submitNewSupplier() {
      try {
        const name = document.getElementById('sName').value.trim();
        const person = document.getElementById('sContact').value.trim();
        const phone = document.getElementById('sPhone').value.trim();
        const email = document.getElementById('sEmail').value.trim();
        const addr = document.getElementById('sAddress').value.trim();

        if (!name) return alert('Supplier name is required!');

        const res = await fetch('/api/add-supplier', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ supplier_name: name, contact_person: person, phone: phone, email: email, address: addr })
        });
        const d = await res.json();
        if (d.status === 'success') {
          closeModal('addSupplierModal');
          document.getElementById('sName').value = '';
          document.getElementById('sContact').value = '';
          document.getElementById('sPhone').value = '';
          document.getElementById('sEmail').value = '';
          document.getElementById('sAddress').value = '';
          await loadAllMasterData();
          alert(`Supplier "${name}" saved to directory!`);
        } else {
          alert('Error saving supplier: ' + (d.message || 'Server error'));
        }
      } catch (err) {
        alert('Request failed: ' + err.message);
      }
    }

    async function submitNewPurchase() {
      try {
        const supId = document.getElementById('purSupplierSelect').value;
        const ref = document.getElementById('purInvoiceRef').value.trim();
        const date = document.getElementById('purDate').value || new Date().toISOString().slice(0, 10);
        const prodId = document.getElementById('purProductSelect').value;
        const qty = parseInt(document.getElementById('purQty').value || 0);
        const cost = parseFloat(document.getElementById('purUnitCost').value || 0);

        if (!prodId || qty <= 0) return alert('Select a product and enter a valid quantity');

        const res = await fetch('/api/add-purchase', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            supplier_id: supId,
            invoice_ref: ref,
            purchase_date: date,
            total_amount: qty * cost,
            items: [{ product_id: prodId, quantity: qty, unit_cost: cost }]
          })
        });
        const d = await res.json();
        if (d.status === 'success') {
          closeModal('addPurchaseModal');
          document.getElementById('purInvoiceRef').value = '';
          document.getElementById('purQty').value = '';
          document.getElementById('purUnitCost').value = '';
          await loadAllMasterData();
          alert(`Inward shipment recorded! Added ${qty} units to stock.`);
        } else {
          alert('Error saving inward purchase: ' + (d.message || 'Server error'));
        }
      } catch (err) {
        alert('Request failed: ' + err.message);
      }
    }

    // ==========================================
    // NLP EXECUTION
    // ==========================================
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
    }

    // ==========================================
    // RE-RENDERING & DATA POPULATION
    // ==========================================
    function renderProductsMasterList() {
      const sortSelect = document.getElementById('catalogSortSelect');
      const sortVal = sortSelect ? sortSelect.value : 'name-asc';
      const sorted = sortItemsList(appData.products || [], sortVal);
      const prodBox = document.getElementById('productsMasterList');
      if (prodBox) {
        prodBox.innerHTML = sorted.map(p => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${p.product_name}</div>
              <div class="text-[11px] text-slate-400">SKU: <span class="font-mono text-teal-300">${p.sku}</span> · Cost: $${p.cost_price.toFixed(2)} · Price: $${p.price.toFixed(2)}</div>
            </div>
            <span class="font-bold px-2.5 py-1 rounded-xl text-xs ${p.stock < 10 ? 'bg-rose-500/20 text-rose-300 font-extrabold' : 'bg-slate-800 text-teal-400'}">${p.stock} in stock</span>
          </div>
        `).join('');
      }
    }

    async function loadAllMasterData() {
      const res = await fetch('/api/master-data');
      appData = await res.json();

      renderCategoryTabs();
      renderFilteredPOS();
      renderProductsMasterList();

      const deptDrop = document.getElementById('staffDeptSelect');
      if (deptDrop) {
        deptDrop.innerHTML = (appData.departments || []).map(d => `<option value="${d.dept_id}">${d.dept_name}</option>`).join('');
      }

      const supDrop = document.getElementById('purSupplierSelect');
      if (supDrop) {
        supDrop.innerHTML = (appData.suppliers || []).map(s => `<option value="${s.supplier_id}">${s.supplier_name}</option>`).join('');
      }

      const prodDrop = document.getElementById('purProductSelect');
      if (prodDrop) {
        prodDrop.innerHTML = (appData.products || []).map(p => `<option value="${p.product_id}">${p.product_name} (${p.sku})</option>`).join('');
      }

      const custDrop = document.getElementById('posCustomerSelect');
      if (custDrop) {
        custDrop.innerHTML = (appData.customers || []).map(c => `<option value="${c.name}">${c.name}</option>`).join('');
      }

      const empBox = document.getElementById('employeesList');
      if (empBox) {
        empBox.innerHTML = (appData.employees || []).map(e => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${e.name}</div>
              <div class="text-[11px] text-purple-400 font-semibold">${e.designation} · <span class="text-slate-400">${e.dept_name}</span></div>
              <div class="text-[10px] text-slate-500 font-mono">${e.email}</div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${e.role === 'admin' ? 'bg-purple-500/20 text-purple-300' : 'bg-teal-500/20 text-teal-300'} capitalize">${e.role}</span>
          </div>
        `).join('');
      }

      const supBox = document.getElementById('suppliersMasterList');
      if (supBox) {
        supBox.innerHTML = (appData.suppliers || []).map(s => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 text-xs space-y-1">
            <div class="font-bold text-white text-sm">${s.supplier_name}</div>
            <div class="text-[11px] text-slate-400">Contact: ${s.contact_person || 'N/A'} · ${s.phone || 'N/A'}</div>
            <div class="text-[10px] text-slate-500">${s.email || ''} · ${s.address || ''}</div>
          </div>
        `).join('');
      }

      const purBox = document.getElementById('purchasesMasterList');
      if (purBox) {
        purBox.innerHTML = (appData.purchases || []).map(pr => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${pr.supplier_name}</div>
              <div class="text-[11px] text-slate-400">Ref: ${pr.invoice_ref} · ${pr.purchase_date}</div>
            </div>
            <span class="font-extrabold text-emerald-400 text-sm">$${pr.total_amount.toFixed(2)}</span>
          </div>
        `).join('');
      }

      const invBox = document.getElementById('inventoryAlertList');
      if (invBox) {
        invBox.innerHTML = (appData.products || []).map(p => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div class="font-semibold text-white">${p.product_name} (${p.category})</div>
            <span class="font-bold text-xs ${p.stock <= 4 ? 'text-rose-400 font-extrabold' : p.stock < 10 ? 'text-amber-400' : 'text-teal-400'}">${p.stock} units</span>
          </div>
        `).join('');
      }

      const slBox = document.getElementById('allSalesList');
      if (slBox) {
        slBox.innerHTML = (appData.sales || []).map(s => `
          <div class="bg-slate-900 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
            <div>
              <div class="font-bold text-white">${s.invoice_no}</div>
              <div class="text-[11px] text-slate-400">${s.sale_date} · Cashier: ${s.cashier_name} · ${s.customer_name}</div>
              <div class="text-[10px] text-teal-400 font-mono mt-0.5">${s.payment_method}</div>
            </div>
            <span class="font-extrabold text-white text-sm">$${s.total_amount.toFixed(2)}</span>
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

print("\nSUCCESS: All form submissions and database syncs repaired!")
