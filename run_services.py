#!/usr/bin/env python3
"""
Dose Services Manager
Starts and manages both Django and Pass-Through services
Date: August 16, 2025
"""

import os
import sys
import time
import socket
import subprocess
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.pass_through_dir = self.base_dir / "pass_through_service"
        self.django_dir = self.base_dir
        self.processes = {}
        
    def check_port(self, port):
        """Check if a port is already in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            return result == 0
    
    def start_pass_through_service(self):
        """Start the pass-through service on port 5000"""
        print("📡 Starting Pass-Through Service (Port 5000)...")
        
        if self.check_port(5000):
            print("⚠️  Port 5000 is already in use. Skipping pass-through service startup.")
            return False
            
        try:
            # Change to pass-through service directory
            os.chdir(self.pass_through_dir)
            
            # Start the pass-through service
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.pass_through_dir
            )
            
            self.processes['pass_through'] = process
            print(f"✅ Pass-Through Service started (PID: {process.pid})")
            
            # Wait a moment for service to initialize
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start pass-through service: {e}")
            return False
    
    def start_django_service(self):
        """Start the Django service on port 8000"""
        print("🌐 Starting Django Service (Port 8000)...")
        
        if self.check_port(8000):
            print("⚠️  Port 8000 is already in use. Skipping Django service startup.")
            return False
            
        try:
            # Change back to Django directory
            os.chdir(self.django_dir)
            
            # Start Django development server
            process = subprocess.Popen(
                [sys.executable, "manage.py", "runserver"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.django_dir
            )
            
            self.processes['django'] = process
            print(f"✅ Django Service started (PID: {process.pid})")
            
            # Wait a moment for service to initialize
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Django service: {e}")
            return False
    
    def check_service_status(self):
        """Check and display the status of both services"""
        print("\n📊 Service Status Check...")
        print("=" * 29)
        
        # Check Pass-Through Service
        if self.check_port(5000):
            print("🟢 Pass-Through Service: RUNNING (Port 5000)")
        else:
            print("🔴 Pass-Through Service: NOT RUNNING")
        
        # Check Django Service  
        if self.check_port(8000):
            print("🟢 Django Service: RUNNING (Port 8000)")
        else:
            print("🔴 Django Service: NOT RUNNING")
        
        print()
    
    def show_service_info(self):
        """Display service URLs and test commands"""
        print("🌐 Service URLs:")
        print("=" * 15)
        print("• Django Admin: http://localhost:8000/admin-panel/")
        print("• Django API: http://localhost:8000/api/")  
        print("• Pass-Through Health: http://localhost:5000/health")
        print("• Test Middleware: http://localhost:8000/test-pass-through")
        print()
        
        print("🧪 Test Commands:")
        print("=" * 16)
        print('curl "http://localhost:8000/test-pass-through"')
        print('curl "http://localhost:5000/health"')
        print()
    
    def monitor_processes(self):
        """Monitor running processes in a separate thread"""
        def monitor():
            while True:
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        print(f"⚠️  {name} service has stopped (exit code: {process.poll()})")
                time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def stop_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping services...")
        
        for name, process in self.processes.items():
            if process.poll() is None:  # Process is still running
                print(f"Stopping {name} service (PID: {process.pid})...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} service stopped")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"🔴 {name} service force killed")
    
    def run(self):
        """Main execution method"""
        print()
        print("🚀 Starting Dose Services...")
        print("=" * 37)
        print()
        
        try:
            # Start services
            pass_started = self.start_pass_through_service()
            django_started = self.start_django_service()
            
            # Show status
            self.check_service_status()
            self.show_service_info()
            
            if pass_started or django_started:
                # Start monitoring
                self.monitor_processes()
                
                print("✨ Services are running! Press Ctrl+C to stop all services.")
                
                # Keep the script running
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        finally:
            self.stop_services()

if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()
