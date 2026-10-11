from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import pymysql.cursors
import csv
import io
from datetime import date
from nlp_engine.parser import NLPQueryParser

app = Flask(__name__)
app.secret_key = "bizcore_desktop_v3_secret_key"

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

# Master Data API with Line-Item Sales Aggregates
@app.route('/api/master-data')
def get_master_data():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Products
            cursor.execute("""
                SELECT p.*, IFNULL(s.supplier_name, 'Direct Supply') AS supplier_name 
                FROM products p 
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id 
                ORDER BY p.product_id DESC
            """)
            products = cursor.fetchall()
            for p in products:
                p['price'] = float(p.get('price') or 0.0)
                p['cost_price'] = float(p.get('cost_price') or 0.0)
                p['reorder_level'] = int(p.get('reorder_level') or 10)
                p['status'] = 'Low stock' if p['stock'] < p['reorder_level'] else 'OK'

            low_stock = [p for p in products if p['stock'] < p['reorder_level']]

            # Sales with Items Sold
            cursor.execute("""
                SELECT s.*, 
                       (SELECT IFNULL(SUM(si.quantity), 0) FROM sale_items si WHERE si.sale_id = s.sale_id) AS items_count
                FROM sales s 
                ORDER BY s.sale_id DESC
            """)
            sales = cursor.fetchall()
            for s in sales:
                s['sale_date'] = s['sale_date'].strftime('%Y-%m-%d')
                s['total_amount'] = float(s['total_amount'])

            # Sale Items for Detailed Category Breakdown
            cursor.execute("""
                SELECT si.quantity, si.unit_price, p.category, s.sale_date
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                JOIN sales s ON si.sale_id = s.sale_id
            """)
            sale_line_items = cursor.fetchall()
            for line in sale_line_items:
                line['sale_date'] = line['sale_date'].strftime('%Y-%m-%d')
                line['unit_price'] = float(line['unit_price'])

            # Customers
            cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
            customers = cursor.fetchall()

            # Employees
            cursor.execute("""
                SELECT e.*, IFNULL(d.dept_name, 'General') AS dept_name, IFNULL(u.role, 'employee') AS role
                FROM employees e
                LEFT JOIN departments d ON e.dept_id = d.dept_id
                LEFT JOIN users u ON e.user_id = u.user_id
                ORDER BY e.employee_id DESC
            """)
            employees = cursor.fetchall()
            for e in employees:
                if e.get('join_date'):
                    e['join_date'] = e['join_date'].strftime('%Y-%m-%d')
                e['monthly_salary'] = float(e.get('monthly_salary') or 0.0)

            # Departments
            cursor.execute("SELECT * FROM departments ORDER BY dept_name ASC")
            departments = cursor.fetchall()

            # Suppliers
            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
            suppliers = cursor.fetchall()

            # Purchases
            cursor.execute("""
                SELECT p.*, IFNULL(s.supplier_name, 'Direct') AS supplier_name 
                FROM purchases p 
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id 
                ORDER BY p.purchase_id DESC
            """)
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
                'sale_line_items': sale_line_items,
                'customers': customers,
                'employees': employees,
                'departments': departments,
                'suppliers': suppliers,
                'purchases': purchases,
                'total_revenue': tot_rev
            })
    finally:
        conn.close()

# CSV Export
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
            return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sales_report.csv"})
    finally:
        conn.close()

# --- CREATE ENDPOINTS ---
@app.route('/api/add-department', methods=['POST'])
def add_dept():
    d = request.get_json() or {}
    name = d.get('dept_name', '').strip()
    if not name: return jsonify({'status': 'error', 'message': 'Department name required'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO departments (dept_name) VALUES (%s)", (name,))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/add-customer', methods=['POST'])
def add_customer():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO customers (name, type, email, phone, city)
                VALUES (%s, %s, %s, %s, %s)
            """, (d.get('name'), d.get('type', 'Retail'), d.get('email'), d.get('phone'), d.get('city', 'Pune')))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/add-product', methods=['POST'])
def add_product():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM products")
            cnt = cursor.fetchone()['cnt']
            sku = (d.get('sku') or '').strip() or f"SKU-{1000 + cnt + 1}"
            cursor.execute("""
                INSERT INTO products (sku, product_name, category, cost_price, price, stock, reorder_level, supplier_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (sku, d.get('product_name'), d.get('category', 'General'), float(d.get('cost_price') or 0), float(d.get('price') or 0), int(d.get('stock') or 0), int(d.get('reorder_level') or 10), d.get('supplier_id') or None))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/add-employee', methods=['POST'])
def add_employee():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (name, email, password, role, designation)
                VALUES (%s, %s, %s, 'employee', %s)
            """, (d.get('name'), d.get('email'), d.get('password') or 'welcome123', d.get('position', 'Staff')))
            u_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO employees (name, email, designation, dept_id, user_id, phone, monthly_salary, join_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (d.get('name'), d.get('email'), d.get('position', 'Staff'), d.get('dept_id') or 1, u_id, d.get('phone'), float(d.get('monthly_salary') or 45000), d.get('join_date') or date.today().strftime('%Y-%m-%d'), d.get('status', 'Active')))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/add-supplier', methods=['POST'])
def add_supplier():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO suppliers (supplier_name, contact_person, phone, email, address)
                VALUES (%s, %s, %s, %s, %s)
            """, (d.get('supplier_name'), d.get('contact_person'), d.get('phone'), d.get('email'), d.get('address')))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/add-purchase', methods=['POST'])
def add_purchase():
    d = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM purchases")
            po = f"PO-{3000 + cursor.fetchone()['cnt'] + 1}"
            cursor.execute("""
                INSERT INTO purchases (po_number, supplier_id, purchase_date, total_amount, quantity, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (po, d.get('supplier_id') or None, d.get('purchase_date') or date.today().strftime('%Y-%m-%d'), float(d.get('total_amount') or 0), int(d.get('quantity') or 1), d.get('status', 'Received')))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

# --- EDIT (CORRECT MISTAKES) ENDPOINTS ---
@app.route('/api/edit-entity', methods=['POST'])
def edit_entity():
    d = request.get_json() or {}
    entity = d.get('entity')
    item_id = d.get('id')
    fields = d.get('fields', {})
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            if entity == 'employee':
                cursor.execute("""
                    UPDATE employees 
                    SET name=%s, designation=%s, dept_id=%s, phone=%s, status=%s, monthly_salary=%s
                    WHERE employee_id=%s
                """, (fields.get('name'), fields.get('designation'), fields.get('dept_id') or 1, fields.get('phone'), fields.get('status', 'Active'), float(fields.get('monthly_salary') or 45000), item_id))
            elif entity == 'product':
                cursor.execute("""
                    UPDATE products 
                    SET product_name=%s, category=%s, price=%s, stock=%s, reorder_level=%s 
                    WHERE product_id=%s
                """, (fields.get('name'), fields.get('category'), float(fields.get('price') or 0), int(fields.get('stock') or 0), int(fields.get('reorder_level') or 10), item_id))
            elif entity == 'customer':
                cursor.execute("""
                    UPDATE customers 
                    SET name=%s, type=%s, email=%s, phone=%s, city=%s 
                    WHERE customer_id=%s
                """, (fields.get('name'), fields.get('type', 'Retail'), fields.get('email'), fields.get('phone'), fields.get('city'), item_id))
            elif entity == 'supplier':
                cursor.execute("""
                    UPDATE suppliers 
                    SET supplier_name=%s, contact_person=%s, phone=%s, email=%s 
                    WHERE supplier_id=%s
                """, (fields.get('name'), fields.get('contact_person'), fields.get('phone'), fields.get('email'), item_id))
            elif entity == 'purchase':
                cursor.execute("""
                    UPDATE purchases 
                    SET total_amount=%s, quantity=%s, status=%s 
                    WHERE purchase_id=%s
                """, (float(fields.get('total_amount') or 0), int(fields.get('quantity') or 1), fields.get('status', 'Received'), item_id))
            conn.commit()
            return jsonify({'status': 'success'})
    finally: conn.close()

# --- DELETE ENDPOINTS ---
@app.route('/api/delete-entity', methods=['POST'])
def delete_entity():
    d = request.get_json() or {}
    entity = d.get('entity')
    item_id = d.get('id')
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            table_map = {
                'employee': ('employees', 'employee_id'),
                'product': ('products', 'product_id'),
                'customer': ('customers', 'customer_id'),
                'supplier': ('suppliers', 'supplier_id'),
                'purchase': ('purchases', 'purchase_id')
            }
            if entity in table_map:
                tbl, col = table_map[entity]
                cursor.execute(f"DELETE FROM {tbl} WHERE {col} = %s", (item_id,))
                conn.commit()
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error', 'message': 'Unknown entity'}), 400
    finally: conn.close()

# --- POS CHECKOUT ---
@app.route('/api/pos-checkout', methods=['POST'])
def pos_checkout():
    d = request.get_json() or {}
    cart = d.get('cart', [])
    if not cart: return jsonify({'status': 'error', 'message': 'Empty cart'}), 400
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM sales")
            inv = f"INV-{5000 + cursor.fetchone()['cnt'] + 1}"
            cursor.execute("""
                INSERT INTO sales (invoice_no, sale_date, customer_name, subtotal, discount, tax, total_amount, change_due, payment_method, payment_breakdown, cashier_name)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (inv, d.get('customer_name', 'Walk-in Customer'), float(d.get('subtotal', 0)), float(d.get('discount', 0)), float(d.get('tax', 0)), float(d.get('total', 0)), float(d.get('change_due', 0)), d.get('payment_summary', 'Cash'), d.get('payment_breakdown', 'Cash'), session['user']['name']))
            sale_id = cursor.lastrowid
            for it in cart:
                cursor.execute("INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)", (sale_id, it['product_id'], int(it['qty']), float(it['price'])))
                cursor.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (int(it['qty']), it['product_id']))
            conn.commit()
            return jsonify({'status': 'success', 'invoice_no': inv})
    finally: conn.close()

# --- NLP QUERY ---
@app.route('/api/nlp-query', methods=['POST'])
def process_nlp():
    data = request.get_json() or {}
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            parser = NLPQueryParser(cursor)
            res = parser.process_query(data.get('query', ''))
        return jsonify({'status': 'success', 'nlp_result': res})
    finally: conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
