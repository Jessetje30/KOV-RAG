#!/bin/bash

# Stop script for RAG Application
# This script stops all running services

set -e

echo "========================================"
echo "Stopping RAG Application"
echo "========================================"
echo ""

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
