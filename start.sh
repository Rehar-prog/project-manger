#!/bin/bash
# Project Control Dashboard - Linux Startup Script
# Usage: ./start.sh

echo "==========================================="
echo "  Project Control Dashboard"
echo "==========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    echo "On Ubuntu/Debian: sudo apt install python3 python3-pip"
    exit 1
fi

# Check Python version (requires 3.8+)
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "ERROR: Python 3.8 or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Python version: $PYTHON_VERSION ✓"
echo ""

# Install/update dependencies
echo "Checking dependencies..."
pip3 install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "WARNING: Some dependencies may have failed to install"
fi

echo ""
echo "Starting Project Control Dashboard..."
echo "Access the dashboard at: http://localhost:8787"
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python3 app.py
