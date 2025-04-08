#!/bin/bash

# Manual starter for CLIPS
cd "$(dirname "$0")"

# Create required directories if they don't exist
mkdir -p logs sessions output temp_uploads

echo "=== CLIPS Manual Startup ==="
echo ""
echo "This script provides instructions for starting CLIPS manually."
echo ""
echo "Step 1: Start the backend server"
echo "  In a terminal window, run:"
echo "  $ python3 backend/main.py"
echo ""
echo "Step 2: Once the backend is running, start the frontend"
echo "  In another terminal window, run:"
echo "  $ npx electron . --external-backend"
echo ""
echo "Would you like me to run Step 1 (start the backend) now? (y/n)"
read -r START_BACKEND

if [[ $START_BACKEND == "y" || $START_BACKEND == "Y" ]]; then
    # Kill any existing processes on port 5000
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    sleep 1
    
    echo "Starting backend server..."
    python3 backend/main.py
fi