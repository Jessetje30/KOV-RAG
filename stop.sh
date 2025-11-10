#!/bin/bash

# Stop script for RAG Application
# This script stops all running services

set -e

echo "========================================"
echo "Stopping RAG Application"
echo "========================================"
echo ""

# Stop Streamlit frontend (if running)
echo "Stopping Streamlit frontend..."
STREAMLIT_PIDS=$(pgrep -f "streamlit run app.py" || true)
if [ -n "$STREAMLIT_PIDS" ]; then
    echo "Found Streamlit processes: $STREAMLIT_PIDS"
    kill $STREAMLIT_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    kill -9 $STREAMLIT_PIDS 2>/dev/null || true
    echo "✓ Streamlit stopped"
else
    echo "No Streamlit processes found"
fi

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "Backend already stopped"
    rm backend.pid
else
    echo "No backend PID file found"
fi

# Stop Qdrant
echo "Stopping Qdrant..."
docker compose down

echo ""
echo "All services stopped successfully!"
echo ""
