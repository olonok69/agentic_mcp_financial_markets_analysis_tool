@echo off
echo Installing Stock Technical Analysis Tool...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Creating environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file from template
) else (
    echo .env file already exists
)

echo.
echo Creating analysis directory...
if not exist analysis mkdir analysis

echo.
echo Installation completed successfully!
echo.
echo Usage:
echo   python stock_analyzer.py AAPL
echo   python analyze.py MSFT
echo.
echo For help: python stock_analyzer.py --help
echo.
pause
