#!/bin/bash

# Startup script for RAG Application
# This script starts Qdrant, backend, and frontend in the correct order

set -e

echo "========================================"
echo "RAG Application Startup Script"
echo "========================================"
echo ""

# Check if backend/.env exists
if [ ! -f backend/.env ]; then
    echo "Error: backend/.env file not found!"
    echo "Please configure backend/.env with your API keys."
    exit 1
fi

# Load backend environment variables
export $(grep -v '^#' backend/.env | xargs)

# Check if OpenAI API key is set (when USE_OPENAI=true)
if [ "$USE_OPENAI" = "true" ]; then
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-openai-api-key-here" ]; then
        echo "Error: OPENAI_API_KEY not set in backend/.env file!"
        echo "Please get your API key from https://platform.openai.com/api-keys"
        exit 1
    fi
    echo "✓ Using OpenAI GPT-5 with text-embedding-3-large"
fi

# Check if JWT secret key is set
if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your_jwt_secret_key_here" ]; then
    echo "Warning: JWT_SECRET_KEY not set in backend/.env file!"
    echo "Generating a new secret key..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$SECRET_KEY/" backend/.env
    echo "Secret key generated and saved to backend/.env"
fi

echo "Step 1: Checking Qdrant vector database..."

# Check if Qdrant is already running
if curl -s http://localhost:6333 > /dev/null 2>&1; then
    echo "✓ Qdrant is already running"
else
    echo "Starting Qdrant..."
    docker compose up -d qdrant

    echo "Waiting for Qdrant to be ready..."
    sleep 5

    # Check if Qdrant is running
    if ! curl -s http://localhost:6333 > /dev/null; then
        echo "Error: Qdrant is not responding!"
        echo "Check Docker logs: docker compose logs qdrant"
        exit 1
    fi
    echo "✓ Qdrant is running"
fi
echo ""

echo "Step 2: Checking FastAPI backend..."

# Check if backend is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is already running"
else
    echo "Starting backend..."
    cd backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install dependencies
    echo "Installing backend dependencies..."
    pip install -q -r requirements.txt

    # Start backend in background
    echo "Starting backend server on http://localhost:8000"
    nohup python main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid

    cd ..

    echo "Waiting for backend to be ready..."
    sleep 5

    # Check if backend is running
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "Warning: Backend may not be ready yet. Check backend.log for details."
    else
        echo "✓ Backend is running"
    fi
fi
echo ""

echo "Step 3: Starting Streamlit frontend..."
cd frontend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing frontend dependencies..."
pip install -q -r requirements.txt

cd ..

echo ""
echo "========================================"
echo "Application started successfully!"
echo "========================================"
echo ""
echo "Access the application at:"
echo "  Frontend: http://localhost:8501"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  Backend: tail -f backend.log"
echo "  Qdrant: docker compose logs -f qdrant"
echo ""
echo "To stop all services:"
echo "  ./stop.sh"
echo ""
echo "Starting Streamlit frontend now..."
echo "(Press Ctrl+C to stop the frontend)"
echo ""

cd frontend
source venv/bin/activate

# Load frontend .env variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

streamlit run app.py
