with open('requirements.txt', 'w') as f:
    f.write("Flask==3.0.3\nPyMySQL==1.1.1\ncryptography==42.0.5\n")

with open('.gitignore', 'w') as f:
    f.write("venv/\n__pycache__/\n*.pyc\n.DS_Store\n*.sqlite3\ninstance/\n.env\n")

with open('run.bat', 'w') as f:
    f.write(
        "@echo off\n"
        "echo ==============================================\n"
        "echo Starting BizCore NLP Business Management System\n"
        "echo ==============================================\n\n"
        "python --version >nul 2>&1\n"
        "if %errorlevel% neq 0 (\n"
        "    echo [ERROR] Python is not installed or not in PATH!\n"
        "    pause\n"
        "    exit /b\n"
        ")\n\n"
        "echo Installing dependencies...\n"
        "pip install -r requirements.txt\n\n"
        "echo Launching Application...\n"
        "python app.py\n"
        "pause\n"
    )

with open('README.md', 'w') as f:
    f.write(
        "# BizCore NLP - Enterprise Business Management System\n\n"
        "A business management portal featuring role-based access, POS checkout, and an NLP query assistant.\n\n"
        "## Setup Instructions\n\n"
        "### 1. Database Setup\n"
        "Import the database dump into MySQL or MariaDB:\n"
        "mysql -u root -p < database/database_setup.sql\n\n"
        "### 2. Run the Application\n"
        "pip install -r requirements.txt\n"
        "python app.py\n\n"
        "Access via browser: http://127.0.0.1:5000\n\n"
        "### Demo Accounts:\n"
        "- Admin: admin@bizcore.dev / admin123\n"
        "- Employee: employee@bizcore.dev / employee123\n"
    )

print("SUCCESS: All project helper files created cleanly!")
