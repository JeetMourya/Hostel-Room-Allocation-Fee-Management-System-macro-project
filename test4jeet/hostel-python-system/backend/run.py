#!/usr/bin/env python3
import subprocess
import sys
import os

def install_requirements():
    print("í³¦ Installing Python requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def start_server():
    print("íº€ Starting Flask server...")
    os.system("python app.py")

if __name__ == "__main__":
    install_requirements()
    start_server()
