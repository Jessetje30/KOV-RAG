#!/bin/bash
cd "/Users/jesse/PycharmProjects/RAG BBL KOV/rag-app"

# Load environment variables
set -a
source backend/.env
set +a

# Kill existing processes
pkill -f "python.*main.py" 2>/dev/null
pkill -f "uvicorn.*main:app" 2>/dev/null
sleep 2

# Start backend
cd backend
source venv/bin/activate
nohup python main.py > ../backend.log 2>&1 &
echo $! > ../backend.pid
echo "Backend started with PID $(cat ../backend.pid)"
