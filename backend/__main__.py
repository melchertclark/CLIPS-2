#!/usr/bin/env python3
"""
Main entry point for running the backend as a module
Usage: python -m backend [port]
"""
import sys
from backend.main import app

def main():
    """Start the Flask app directly"""
    # Use the provided port or default to 5000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Starting CLIPS backend on port {port}")
    print(f"Running on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)

if __name__ == "__main__":
    main()