#!/bin/bash

# This script starts the backend and frontend separately
cd "$(dirname "$0")"

# Make sure script is executable
chmod +x start_backend.py

# Ensure virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create required directories if they don't exist
mkdir -p logs sessions output temp_uploads

# Verify Python is available
if command -v python3 &> /dev/null; then
    echo "Using python3"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "Using python"
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Start the backend directly
echo "Starting backend server..."
$PYTHON_CMD start_backend.py 5000 &
BACKEND_PID=$!

# Wait for the backend to start
sleep 3

# Start the frontend
echo "Starting frontend..."
npx electron . --debug

# Kill the backend when the frontend exits
kill $BACKEND_PID