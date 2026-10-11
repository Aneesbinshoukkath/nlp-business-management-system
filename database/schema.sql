DROP DATABASE IF EXISTS business_management;
CREATE DATABASE business_management;
USE business_management;

CREATE USER IF NOT EXISTS 'biz_user'@'localhost' IDENTIFIED BY 'biz_pass123';
GRANT ALL PRIVILEGES ON business_management.* TO 'biz_user'@'localhost';
FLUSH PRIVILEGES;

-- Users Table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('admin', 'employee') NOT NULL
);

-- Departments Table
CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL
);

-- Employees Table
CREATE TABLE employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    designation VARCHAR(100),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
);

-- Products Table
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0
);

-- Sales / Invoices Table
CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(50) NOT NULL,
    sale_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50)
);

-- Sale Items Table
CREATE TABLE sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT,
    product_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 1. Insert Users Matching the Demo Screen
INSERT INTO users (name, email, password, role) VALUES
('Admin User', 'admin@bizcore.dev', 'admin123', 'admin'),
('Priya Nair', 'employee@bizcore.dev', 'employee123', 'employee');

-- 2. Insert Departments & Employees
INSERT INTO departments (dept_id, dept_name) VALUES
(1, 'Sales'), (2, 'Inventory'), (3, 'Human Resources'), (4, 'IT Support');

INSERT INTO employees (name, email, designation, dept_id) VALUES
('Priya Nair', 'employee@bizcore.dev', 'Operations Executive', 1),
('Rahul Sharma', 'rahul@bizcore.dev', 'Sales Lead', 1),
('Kiran Kumar', 'kiran@bizcore.dev', 'Inventory Manager', 2),
('Sneha Patil', 'sneha@bizcore.dev', 'HR Generalist', 3);

-- 3. Insert 16 Products (Including the 8 Low-Stock Items on Screen)
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
('Cat6 Ethernet Cable (50m)', 'Networking', 35.00, 40),
('USB-C 100W Hub', 'Accessories', 45.00, 30),
('Samsung T7 1TB SSD', 'Storage', 130.00, 22),
('Wireless Presenter Clicker', 'Accessories', 25.00, 15),
('Smart Surge Protector', 'Hardware', 40.00, 19);

-- 4. Insert Recent Transactions Matching Screen
INSERT INTO sales (invoice_no, sale_date, total_amount, payment_method) VALUES
('INV-5000', '2026-10-10', 267.00, 'Card'),
('INV-5001', '2026-10-10', 198.00, 'UPI'),
('INV-5002', '2026-10-10', 1145.00, 'Wire'),
('INV-5003', '2026-10-10', 2730.00, 'Card'),
('INV-5004', '2026-10-10', 200.00, 'Cash'),
('INV-5032', '2026-10-10', 1199.00, 'Card');

-- Add top product sales link
INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES
(6, 2, 1, 1199.00),
(4, 1, 2, 1100.00);
