#!/usr/bin/env python3
import os
import sys
import webbrowser

def start_system():
    print("íº€ Starting Hostel Management System (Simple Mode)...")
    
    # Start MySQL if not running
    if os.system("docker ps | grep hostel-mysql") != 0:
        print("Starting MySQL database...")
        os.system("docker-compose up -d")
        import time
        time.sleep(10)
    
    # Start Python backend
    print("Starting Python backend...")
    os.chdir("backend")
    
    # Check if venv exists, if not install requirements globally
    if not os.path.exists("venv"):
        print("Installing Python packages...")
        os.system("pip install -r requirements.txt")
    
    # Start Flask app
    print("Flask app starting on http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Open browser
    webbrowser.open("http://localhost:5000")
    
    # Run app
    os.system("python app.py")

if __name__ == "__main__":
    start_system()
