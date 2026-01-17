import psutil
import time


def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")


def find_and_kill_blacklisted_process(blacklisted_processes: list[str]) -> None:
    log("Checking for blacklisted processes...")
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        for name in blacklisted_processes:
            exe_lower = proc.info["exe"].lower() if proc.info["exe"] else ""
            if name.lower() in exe_lower:
                log(f"Found blacklisted process: {proc.info['exe']}")
                terminate_blacklisted_process(
                    proc.info["pid"], proc.info["name"], proc.info["exe"]
                )
    return None


def terminate_blacklisted_process(pid: int, name: str, exe: str) -> None:
    try:
        log(f"Attempting to terminate process: {pid} {name} {exe}")
        proc = psutil.Process(pid)
        proc.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        log(f"Could not terminate process with PID, name and exe: {pid, name, exe}")


def main(blacklisted_processes: list[str], dev_mode) -> None:
    if dev_mode != "1":
        log(
            "Blacklist process started with blacklisted processes: "
            + ", ".join(blacklisted_processes)
        )
        while True:
            find_and_kill_blacklisted_process(blacklisted_processes)
            time.sleep(10)


if __name__ == "__main__":
    main()
