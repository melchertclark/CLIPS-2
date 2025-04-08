#!/bin/bash

# Script to only start the Electron frontend when the backend is already running
cd "$(dirname "$0")"

if [ ! -f "backend_port.txt" ]; then
  echo "ERROR: No backend_port.txt file found. Start the backend first with: python3 backend/main.py"
  exit 1
fi

PORT=$(cat backend_port.txt)
echo "Found backend port: $PORT, starting Electron frontend..."

# Start Electron with the external backend flag
ELECTRON_ENABLE_LOGGING=1 npx electron . --external-backend