#!/bin/bash

# Simple script for CLIPS
cd "$(dirname "$0")"

# Kill processes if any
pkill -f "python3 backend/main.py" 2>/dev/null || true

# Start backend
echo "Starting backend..."
python3 backend/main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Wait for backend to create port file
echo "Waiting for backend to initialize..."
for i in {1..10}; do
  if [ -f "backend_port.txt" ]; then
    PORT=$(cat backend_port.txt)
    echo "Backend is running on port $PORT"
    break
  fi
  echo "Waiting... ($i/10)"
  sleep 1
done

# Verify backend is still running
if ! ps -p $BACKEND_PID > /dev/null; then
  echo "ERROR: Backend process has died. Check backend.log for details"
  exit 1
fi

echo "Starting frontend..."
cd "$(dirname "$0")"
npx electron . --external-backend

# When electron exits, kill the backend
kill $BACKEND_PID 2>/dev/null || true
echo "Done"