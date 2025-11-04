#!/bin/bash

# Restart script for RAG Application
# This script stops all services and starts them again

set -e

echo "========================================"
echo "Restarting RAG Application"
echo "========================================"
echo ""

# Stop services
./stop.sh

echo ""
echo "Waiting 3 seconds before restart..."
sleep 3
echo ""

# Start services
./start.sh
