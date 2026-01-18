"""
Django Management Command: runservices
Starts both Django and Pass-Through services together
Usage: python manage.py runservices
"""

import os
import sys
import time
import socket
import signal
import subprocess
import threading
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Start both Django and Pass-Through services together'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processes = {}
        self.running = True
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--django-port',
            type=int,
            default=8000,
            help='Port for Django server (default: 8000)'
        )
        parser.add_argument(
            '--passthrough-port', 
            type=int,
            default=5000,
            help='Port for Pass-Through service (default: 5000)'
        )
        parser.add_argument(
            '--no-passthrough',
            action='store_true',
            help='Skip starting the pass-through service'
        )
        
    def check_port(self, port):
        """Check if a port is already in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', port))
            return result == 0
    
    def start_pass_through_service(self, port=5000):
        """Start the pass-through service"""
        self.stdout.write("📡 Starting Pass-Through Service (Port {})...".format(port))
        
        if self.check_port(port):
            self.stdout.write(
                self.style.WARNING("⚠️  Port {} is already in use. Skipping pass-through service.".format(port))
            )
            return False
            
        try:
            # Get the pass-through service directory
            # BASE_DIR should be DoseV3Master, so pass_through_service should be directly in it
            base_dir = Path(settings.BASE_DIR)
            pass_through_dir = base_dir / "pass_through_service"
            
            if not pass_through_dir.exists():
                self.stdout.write(
                    self.style.ERROR("❌ Pass-through service directory not found: {}".format(pass_through_dir))
                )
                return False
            
            # Start the pass-through service
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(pass_through_dir)
            )
            
            self.processes['pass_through'] = process
            self.stdout.write(
                self.style.SUCCESS("✅ Pass-Through Service started (PID: {})".format(process.pid))
            )
            
            # Wait a moment for service to initialize
            time.sleep(2)
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("❌ Failed to start pass-through service: {}".format(e))
            )
            return False
    
    def start_django_service(self, port=8000):
        """Start Django development server"""
        self.stdout.write("🌐 Starting Django Service (Port {})...".format(port))
        
        if self.check_port(port):
            self.stdout.write(
                self.style.WARNING("⚠️  Port {} is already in use. Skipping Django service.".format(port))
            )
            return False
            
        try:
            # Start Django development server
            process = subprocess.Popen(
                [sys.executable, "manage.py", "runserver", "127.0.0.1:{}".format(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path(settings.BASE_DIR))
            )
            
            self.processes['django'] = process
            self.stdout.write(
                self.style.SUCCESS("✅ Django Service started (PID: {})".format(process.pid))
            )
            
            # Wait a moment for service to initialize
            time.sleep(3)
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("❌ Failed to start Django service: {}".format(e))
            )
            return False
    
    def check_service_status(self, django_port=8000, passthrough_port=5000):
        """Check and display service status"""
        self.stdout.write("\n📊 Service Status Check...")
        self.stdout.write("=" * 29)
        
        # Check Pass-Through Service
        if self.check_port(passthrough_port):
            self.stdout.write(
                self.style.SUCCESS("🟢 Pass-Through Service: RUNNING (Port {})".format(passthrough_port))
            )
        else:
            self.stdout.write(
                self.style.ERROR("🔴 Pass-Through Service: NOT RUNNING")
            )
        
        # Check Django Service
        if self.check_port(django_port):
            self.stdout.write(
                self.style.SUCCESS("🟢 Django Service: RUNNING (Port {})".format(django_port))
            )
        else:
            self.stdout.write(
                self.style.ERROR("🔴 Django Service: NOT RUNNING")
            )
        
        self.stdout.write("")
    
    def show_service_info(self, django_port=8000, passthrough_port=5000):
        """Display service URLs and commands"""
        self.stdout.write("🌐 Service URLs:")
        self.stdout.write("=" * 15)
        self.stdout.write("• Django Admin: http://localhost:{}/admin-panel/".format(django_port))
        self.stdout.write("• Django API: http://localhost:{}/api/".format(django_port))
        self.stdout.write("• Pass-Through Health: http://localhost:{}/health".format(passthrough_port))
        self.stdout.write("• Test Middleware: http://localhost:{}/test-pass-through".format(django_port))
        self.stdout.write("")
        
        self.stdout.write("🧪 Test Commands:")
        self.stdout.write("=" * 16)
        self.stdout.write('curl "http://localhost:{}/test-pass-through"'.format(django_port))
        self.stdout.write('curl "http://localhost:{}/health"'.format(passthrough_port))
        self.stdout.write("")
    
    def monitor_processes(self):
        """Monitor running processes"""
        def monitor():
            while self.running:
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        self.stdout.write(
                            self.style.WARNING("⚠️  {} service has stopped (exit code: {})".format(
                                name, process.poll()
                            ))
                        )
                        # Remove stopped process from tracking
                        del self.processes[name]
                time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def stop_services(self):
        """Stop all running services"""
        self.running = False
        
        if self.processes:
            self.stdout.write("\n🛑 Stopping services...")
            
            for name, process in self.processes.items():
                if process.poll() is None:  # Process is still running
                    self.stdout.write("Stopping {} service (PID: {})...".format(name, process.pid))
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                        self.stdout.write(
                            self.style.SUCCESS("✅ {} service stopped".format(name))
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        self.stdout.write(
                            self.style.ERROR("🔴 {} service force killed".format(name))
                        )
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write("\n\n🛑 Received shutdown signal...")
        self.stop_services()
        sys.exit(0)
    
    def handle(self, *args, **options):
        """Main command handler"""
        django_port = options['django_port']
        passthrough_port = options['passthrough_port']
        skip_passthrough = options['no_passthrough']
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        self.stdout.write("")
        self.stdout.write("🚀 Starting Dose Services...")
        self.stdout.write("=" * 37)
        self.stdout.write("")
        
        try:
            services_started = False
            
            # Start pass-through service (unless skipped)
            if not skip_passthrough:
                if self.start_pass_through_service(passthrough_port):
                    services_started = True
            
            # Start Django service
            if self.start_django_service(django_port):
                services_started = True
            
            if not services_started:
                self.stdout.write(
                    self.style.ERROR("❌ No services were started. Check port availability.")
                )
                return
            
            # Show status and info
            self.check_service_status(django_port, passthrough_port)
            self.show_service_info(django_port, passthrough_port)
            
            # Start monitoring
            self.monitor_processes()
            
            self.stdout.write(
                self.style.SUCCESS("✨ Services are running! Press Ctrl+C to stop all services.")
            )
            
            # Keep the command running
            try:
                while self.running and self.processes:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("❌ Error: {}".format(e))
            )
            
        finally:
            self.stop_services()
