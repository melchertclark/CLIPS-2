#!/bin/bash

# Start the application
cd "$(dirname "$0")"

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

# Verify pip is available
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo "Error: pip not found. Please install pip."
    exit 1
fi

# Install required Python packages if not already installed
$PIP_CMD install -r requirements.txt

# Start the application
npm start