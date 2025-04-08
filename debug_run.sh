#!/bin/bash

# Debug script for CLIPS
cd "$(dirname "$0")"

# Create required directories
mkdir -p logs sessions output temp_uploads

# Kill any existing Python processes on ports
echo "Checking for existing processes..."
pkill -f "python.*backend/main.py" 2>/dev/null || true

# Remove any existing port file
rm -f backend_port.txt

echo "=== STEP 1: Starting backend ==="
python3 backend/main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for port file
echo "Waiting for port file..."
for i in {1..10}; do
  if [ -f "backend_port.txt" ]; then
    echo "Port file found!"
    PORT=$(cat backend_port.txt)
    echo "Backend running on port: $PORT"
    break
  fi
  echo "Waiting... ($i/10)"
  sleep 1
done

if [ ! -f "backend_port.txt" ]; then
  echo "ERROR: Port file not created. Check backend.log"
  cat backend.log
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

echo "=== STEP 2: Starting Electron ==="
echo "Running: npx electron . --external-backend"
npx electron . --external-backend > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo "=== Application is starting ==="
echo "Backend PID: $BACKEND_PID (logs in backend.log)"
echo "Frontend PID: $FRONTEND_PID (logs in frontend.log)"
echo ""
echo "Press Enter to stop and view logs..."
read -r

echo "Stopping processes..."
kill $FRONTEND_PID $BACKEND_PID 2>/dev/null || true

echo "=== Backend Log ==="
cat backend.log

echo ""
echo "=== Frontend Log ==="
cat frontend.log