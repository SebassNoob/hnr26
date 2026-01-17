import psutil
import time

def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")

def check_for_blacklisted_process(blacklisted_processes: list[str]) -> list[int]:
    blacklisted_pids = []
    for proc in psutil.process_iter(["pid", "name"]):
        for name in blacklisted_processes:
            log(proc.info["name"].lower())
            if proc.info["name"].lower() in name:
                log("Found blacklisted process: " + proc.info["name"])
                blacklisted_pids.append(int(proc.info["pid"]))
    log(f"Blacklisted processes found: {blacklisted_pids}")
    return blacklisted_pids


def terminate_blacklisted_processes(blacklisted_processes: list[int]) -> None:
    for pid in blacklisted_processes:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print("Could not terminate process with PID:", pid)
            continue


def main(blacklisted_processes: list[str], dev_mode) -> None:
    if dev_mode != '1':
        log("Blacklist process started with blacklisted processes: " + ", ".join(blacklisted_processes))
        while True:
            running_blacklisted = check_for_blacklisted_process(blacklisted_processes)
            if running_blacklisted != []:
                terminate_blacklisted_processes(blacklisted_processes)
            time.sleep(60)


if __name__ == "__main__":
    main()
