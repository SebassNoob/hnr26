"""Hot reload script for development"""

import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PythonFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart()

    def restart(self):
        if self.process:
            print("\n🔄 Restarting application...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        print("🚀 Starting application...")
        self.process = subprocess.Popen(
            [sys.executable, "src/main.py"], cwd=Path(__file__).parent
        )

    def on_modified(self, event):
        if event.src_path.endswith(".py") and not event.is_directory:
            print(f"📝 File changed: {event.src_path}")
            self.restart()


if __name__ == "__main__":
    src_path = Path(__file__).parent / "src"
    print(f"👀 Watching {src_path} for changes...")
    print("Press Ctrl+C to stop\n")

    event_handler = PythonFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(src_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()

    observer.join()
