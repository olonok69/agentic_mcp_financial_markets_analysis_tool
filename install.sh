#!/bin/bash

echo "Installing Stock Technical Analysis Tool..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found. Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo
echo "Creating environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template"
else
    echo ".env file already exists"
fi

echo
echo "Creating analysis directory..."
mkdir -p analysis

echo
echo "Making scripts executable..."
chmod +x stock_analyzer.py
chmod +x analyze.py

echo
echo "Installation completed successfully!"
echo
echo "Usage:"
echo "  python3 stock_analyzer.py AAPL"
echo "  python3 analyze.py MSFT"
echo
echo "For help: python3 stock_analyzer.py --help"
echo
