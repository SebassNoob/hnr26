import win32gui
import win32process
import psutil


def get_active_process_info():
    hwnd = win32gui.GetForegroundWindow()

    # Get the Process ID (PID) from the window handle
    _, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        # Use psutil to get the process name from the PID
        process = psutil.Process(pid)
        return {
            "title": win32gui.GetWindowText(hwnd),
            "name": process.name(),
            "pid": pid,
        }
    except psutil.NoSuchProcess:
        return None


def main():
    pass


if __name__ == "__main__":
    main()
