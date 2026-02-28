#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def print_step(step, message):
    print(f"\n{'='*50}")
    print(f"Step {step}: {message}")
    print('='*50)

def run_command(command, check=True):
    """Run a shell command."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is installed and running."""
    print_step(1, "Checking Docker Installation")
    if not run_command("docker --version", check=False):
        print("‚ùå Docker is not installed!")
        print("Please install Docker from: https://www.docker.com/products/docker-desktop")
        print("For Linux: sudo apt install docker.io docker-compose")
        return False
    print("‚úÖ Docker is installed")
    return True

def start_mysql():
    """Start MySQL database using Docker."""
    print_step(2, "Starting MySQL Database")
    
    # Stop any existing hostel containers
    run_command("docker stop hostel-mysql hostel-phpmyadmin 2>/dev/null || true", check=False)
    run_command("docker rm hostel-mysql hostel-phpmyadmin 2>/dev/null || true", check=False)
    
    # Start new containers
    if run_command("docker-compose up -d"):
        print("‚è≥ Waiting for MySQL to start (15 seconds)...")
        time.sleep(15)
        
        # Verify MySQL is running
        if run_command("docker ps | grep hostel-mysql", check=False):
            print("‚úÖ MySQL database is running on port 3306")
            print("‚úÖ phpMyAdmin is running on http://localhost:8080")
            print("   - Username: root")
            print("   - Password: root123")
            return True
        else:
            print("‚ùå MySQL failed to start. Check logs: docker logs hostel-mysql")
            return False
    return False

def setup_python_backend():
    """Setup Python backend environment."""
    print_step(3, "Setting up Python Backend")
    
    os.chdir("backend")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command("python -m venv venv")
    
    # Activate venv and install requirements
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate && "
    else:
        activate_cmd = "source venv/bin/activate && "
    
    print("Installing Python packages...")
    run_command(f"{activate_cmd}pip install --upgrade pip")
    
    if run_command(f"{activate_cmd}pip install -r requirements.txt"):
        print("‚úÖ Python backend setup complete")
        os.chdir("..")
        return True
    
    os.chdir("..")
    return False

def check_ports():
    """Check if required ports are available."""
    print_step(4, "Checking Port Availability")
    
    ports = [3306, 5000, 8080]
    for port in ports:
        if sys.platform == "win32":
            cmd = f"netstat -an | findstr :{port}"
        else:
            cmd = f"lsof -i:{port} 2>/dev/null | grep LISTEN"
        
        if run_command(cmd, check=False):
            print(f"‚ö†Ô∏è  Port {port} is in use")
        else:
            print(f"‚úÖ Port {port} is available")
    
    return True

def create_shortcuts():
    """Create shortcut scripts for easy startup."""
    print_step(5, "Creating Shortcut Scripts")
    
    # Create start script for Windows
    if sys.platform == "win32":
        with open("start_hostel.bat", "w") as f:
            f.write("""@echo off
echo Starting Hostel Management System...
echo.

echo Step 1: Starting MySQL Database...
docker-compose up -d
timeout /t 10 /nobreak >nul

echo Step 2: Starting Python Backend...
cd backend
call venv\\Scripts\\activate
start python app.py
cd ..

echo Step 3: Opening Frontend...
start frontend/index.html

echo.
echo ‚úÖ System started successfully!
echo.
echo Access Points:
echo - Frontend: http://localhost:5000 (auto-open)
echo - API: http://localhost:5000
echo - phpMyAdmin: http://localhost:8080 (user: root, pass: root123)
echo.
pause
""")
        print("‚úÖ Created start_hostel.bat")
    
    # Create start script for Linux/Mac
    with open("start_hostel.sh", "w") as f:
        f.write("""#!/bin/bash
echo "Starting Hostel Management System..."
echo

echo "Step 1: Starting MySQL Database..."
docker-compose up -d
sleep 10

echo "Step 2: Starting Python Backend..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

echo "Step 3: Opening Frontend..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:5000"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "http://localhost:5000" 2>/dev/null || true
fi

echo
echo "‚úÖ System started successfully!"
echo
echo "Access Points:"
echo "- Frontend: http://localhost:5000"
echo "- API Documentation: http://localhost:5000"
echo "- phpMyAdmin: http://localhost:8080"
echo "  - Username: root"
echo "  - Password: root123"
echo
echo "Press Ctrl+C to stop the system"
echo

wait $BACKEND_PID
""")
    
    run_command("chmod +x start_hostel.sh")
    print("‚úÖ Created start_hostel.sh")

def main():
    print("Ì∫Ä Hostel Management System - Complete Setup")
    print("Technology Stack: Python Flask + MySQL + HTML Frontend")
    
    # Check prerequisites
    if not check_docker():
        sys.exit(1)
    
    if not check_ports():
        sys.exit(1)
    
    # Start database
    if not start_mysql():
        sys.exit(1)
    
    # Setup Python backend
    if not setup_python_backend():
        sys.exit(1)
    
    # Create shortcuts
    create_shortcuts()
    
    print("\n" + "="*60)
    print("Ìæâ SETUP COMPLETE!")
    print("="*60)
    print("\nÌ≥ã To start the system:")
    
    if sys.platform == "win32":
        print("   Double-click: start_hostel.bat")
        print("   OR Run in terminal: start_hostel.bat")
    else:
        print("   Run in terminal: ./start_hostel.sh")
    
    print("\nÌºê Access Points:")
    print("   - Frontend: http://localhost:5000")
    print("   - API Documentation: http://localhost:5000")
    print("   - phpMyAdmin: http://localhost:8080")
    print("     ‚Ä¢ Username: root")
    print("     ‚Ä¢ Password: root123")
    
    print("\nÌ∞≥ Docker Commands:")
    print("   - View logs: docker logs hostel-mysql")
    print("   - Stop system: docker-compose down")
    
    print("\nÌ∞ç Python Backend Commands:")
    print("   - Manual start: cd backend && python app.py")
    print("   - Install packages: pip install -r requirements.txt")
    
    print("\nÌ≤° Quick Test:")
    print("   curl http://localhost:5000/health")
    print("   Should return: {\"status\": \"Running\", ...}")

if __name__ == "__main__":
    main()
