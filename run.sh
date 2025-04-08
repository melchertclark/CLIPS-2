#!/bin/bash

# Start the application
cd "$(dirname "$0")"

# Ensure virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

npm start