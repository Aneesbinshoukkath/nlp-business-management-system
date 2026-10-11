USE business_management;

-- 1. Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100)
);

-- 2. Purchases Table
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    purchase_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Received',
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);

-- Mock Data for Suppliers & Purchases
INSERT INTO suppliers (supplier_name, contact_person, phone, email) VALUES
('TechSource Solutions', 'Kavya Rao', '+91 98450 11223', 'orders@techsource.in'),
('Prime Office Furnishings', 'Manish Sen', '+91 98711 33445', 'sales@primefurnish.com');

INSERT INTO purchases (supplier_id, purchase_date, total_amount, status) VALUES
(1, '2026-10-01', 4400.00, 'Received'),
(2, '2026-10-05', 1100.00, 'Received');
