#!/bin/bash

# Simple starter script for CLIPS
cd "$(dirname "$0")"

# Create required directories
mkdir -p logs sessions output temp_uploads

echo "Starting CLIPS..."

# Stop any running processes
pkill -f "python.*backend/main.py" 2>/dev/null || true
rm -f backend_port.txt

# Start backend server
echo "Starting backend server..."
python3 backend/main.py &
BACKEND_PID=$!

# Wait for port file
echo "Waiting for port file..."
for i in {1..10}; do
  if [ -f "backend_port.txt" ]; then
    PORT=$(cat backend_port.txt)
    echo "Backend running on port: $PORT"
    break
  fi
  sleep 1
  echo "Waiting... ($i/10)"
done

# Verify backend is running
if [ ! -f "backend_port.txt" ]; then
  echo "ERROR: Backend failed to create port file"
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

# Start frontend
echo "Starting frontend..."
npx electron . --external-backend

# Clean up
kill $BACKEND_PID 2>/dev/null || true
echo "Shutdown complete"