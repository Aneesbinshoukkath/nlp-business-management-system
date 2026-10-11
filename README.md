# BizCore NLP - Enterprise Business Management System

A business management portal featuring role-based access, POS checkout, and an NLP query assistant.

## Setup Instructions

### 1. Database Setup
Import the database dump into MySQL or MariaDB:
mysql -u root -p < database/database_setup.sql

### 2. Run the Application
pip install -r requirements.txt
python app.py

Access via browser: http://127.0.0.1:5000

### Demo Accounts:
- Admin: admin@bizcore.dev / admin123
- Employee: employee@bizcore.dev / employee123
