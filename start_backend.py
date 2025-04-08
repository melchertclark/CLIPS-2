#!/usr/bin/env python3
"""
Simple script to start the CLIPS backend server
"""
import os
import sys
import subprocess

def main():
    # Get the absolute path to the backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    main_script = os.path.join(backend_dir, "main.py")
    
    # Ensure the script exists
    if not os.path.exists(main_script):
        print(f"Error: Backend script not found at {main_script}")
        return 1
    
    # Use the provided port or default to 5000
    port = sys.argv[1] if len(sys.argv) > 1 else "5000"
    
    print(f"Starting CLIPS backend at {main_script} on port {port}")
    
    # Make sure required directories exist
    for dirname in ["logs", "sessions", "output", "temp_uploads"]:
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), dirname), exist_ok=True)
    
    # Start the backend script
    try:
        # Print the ready message directly first
        print(f"Running on http://127.0.0.1:{port}")
        
        # Execute the main.py directly
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from backend.main import app
        app.run(host='127.0.0.1', port=int(port), debug=True)
        
    except Exception as e:
        print(f"Error starting backend: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())