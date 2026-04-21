#!/usr/bin/env python3
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def install_requirements():
    print("📦 Installing Python requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    print("🚀 Starting Flask server...")
    
    # Check if we should run the old app.py or the new structured format
    if os.environ.get('FLASK_APP'):
        os.system("flask run")
    else:
        # Default starting point
        from app import create_app
        app = create_app()
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--install':
        install_requirements()
    
    start_server()

