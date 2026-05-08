@echo off
REM Quick setup and start script for Windows

echo.
echo ================================
echo AI Agent Setup
echo ================================
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.9+
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo Warning: Please edit .env file and add your CLAUDE_API_KEY
)

REM Create data directories
if not exist "data\memories" mkdir data\memories
if not exist "data\vectors" mkdir data\vectors
if not exist "logs" mkdir logs

echo.
echo ================================
echo Setup completed successfully!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env file and add your CLAUDE_API_KEY
echo 2. Run 'python test.py' to test the system
echo 3. Run 'python server.py' to start the server
echo.

pause
