#!/bin/bash

# Startup script for UI development on port 8502
# This allows running the UI branch alongside the main app

set -e

echo "========================================"
echo "UI Development - Port 8502"
echo "========================================"
echo ""

cd frontend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Load frontend .env variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting Streamlit on port 8502..."
echo "UI Dev: http://localhost:8502"
echo "Main App: http://localhost:8501"
echo ""

streamlit run app.py --server.port 8502
