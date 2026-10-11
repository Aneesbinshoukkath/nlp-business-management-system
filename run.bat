@echo off
echo ==============================================
echo Starting BizCore NLP Business Management System
echo ==============================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b
)

echo Installing dependencies...
pip install -r requirements.txt

echo Launching Application...
python app.py
pause
