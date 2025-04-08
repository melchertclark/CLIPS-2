#!/bin/bash

# Manual step-by-step CLIPS starter
cd "$(dirname "$0")"

echo "===== CLIPS MANUAL STARTUP ====="
echo "This script will guide you through starting CLIPS step by step."
echo ""

# Create required directories
mkdir -p logs sessions output temp_uploads

# Kill any existing processes
echo "Stopping any existing Python processes..."
pkill -f "python.*backend/main.py" 2>/dev/null || true
rm -f backend_port.txt

echo ""
echo "STEP 1: Start the backend"
echo "  Running the command: python3 backend/main.py"
echo "  You should see 'Running on http://127.0.0.1:3000' and a port number."
echo "  The backend_port.txt file should be created."
echo ""
echo "Press Enter to run the backend..."
read -r

python3 backend/main.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

echo ""
echo "Waiting for backend to initialize..."
for i in {1..10}; do
  if [ -f "backend_port.txt" ]; then
    PORT=$(cat backend_port.txt)
    echo "Success! Backend is running on port $PORT"
    break
  fi
  sleep 1
  echo "Waiting... ($i/10)"
done

if [ ! -f "backend_port.txt" ]; then
  echo "ERROR: Backend did not create port file. Something is wrong."
  kill $BACKEND_PID 2>/dev/null || true
  exit 1
fi

echo ""
echo "STEP 2: Test backend connectivity"
echo "  Running a simple Node.js script to test the backend API"
echo "  This will verify if the backend is responding correctly."
echo ""
echo "Press Enter to test backend connectivity..."
read -r

node backend_test.js

echo ""
echo "STEP 3: Start the Electron frontend"
echo "  Running the command: npx electron . --external-backend"
echo "  This will connect to the running backend."
echo ""
echo "Press Enter to start the frontend..."
read -r

npx electron . --external-backend

# Clean up when Electron exits
kill $BACKEND_PID 2>/dev/null || true
echo "CLIPS has exited"