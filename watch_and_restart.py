import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class RestartServerHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart_server()

    def restart_server(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Restarting Django server...")
        self.process = subprocess.Popen(self.command, shell=True)

    def on_any_event(self, event):
        if event.is_directory:
            return
        print(f"File changed: {event.src_path}")
        self.restart_server()

if __name__ == "__main__":
    path = os.getcwd()
    command = "python manage.py runserver"  # You can customize the port if needed
    event_handler = RestartServerHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Watching for changes in {path}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    if event_handler.process:
        event_handler.process.terminate()
        event_handler.process.wait()
