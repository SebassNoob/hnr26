import psutil
import time


def check_for_blacklisted_process(blacklisted_processes: list[str]) -> list[int]:
    blacklisted_pids = []
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"].lower() in (
            name.lower() for name in blacklisted_processes
        ):
            blacklisted_pids.append(int(proc.info["pid"]))
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
        while True:
            running_blacklisted = check_for_blacklisted_process(blacklisted_processes)
            if running_blacklisted != []:
                terminate_blacklisted_processes(blacklisted_processes)
            time.sleep(60)


if __name__ == "__main__":
    main()
