#!/bin/bash

# Direct starter script for CLIPS - starts backend manually
cd "$(dirname "$0")"

# Create required directories if they don't exist
mkdir -p logs sessions output temp_uploads

# Clear any existing Python processes on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start the backend directly in a separate process
echo "Starting backend..."
cd "$(dirname "$0")"
python3 backend/main.py &
BACKEND_PID=$!

# Wait for the backend to start
echo "Waiting for backend to start..."
sleep 3

# Start the frontend with external backend flag
echo "Starting frontend..."
cd "$(dirname "$0")"
npx electron . --external-backend

# Kill the backend when the frontend exits
echo "Stopping backend process..."
kill $BACKEND_PID 2>/dev/null || echo "Backend already stopped."