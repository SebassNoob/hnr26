import psutil
import time
from utils import log
import asyncio


def find_and_kill_blacklisted_process(blacklisted_processes: list[str]) -> None:
    to_delete = []
    log("Checking for blacklisted processes...")
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        for name in blacklisted_processes:
            exe_lower = proc.info["exe"].lower() if proc.info["exe"] else ""
            if name.lower() in exe_lower:
                log(f"Found blacklisted process: {proc.info['exe']}")
                to_delete.append(proc)
    asyncio.gather(
        *[
            terminate_blacklisted_process(
                proc.info["pid"], proc.info["name"], proc.info["exe"]
            )
            for proc in to_delete
        ]
    )

    return None


async def terminate_blacklisted_process(pid: int, name: str, exe: str) -> None:
    loop = asyncio.get_event_loop()
    try:
        log(f"Attempting to terminate process: {pid} {name} {exe}")
        proc = psutil.Process(pid)
        await loop.run_in_executor(None, proc.terminate)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        log(f"Could not terminate process with PID, name and exe: {pid, name, exe}")
    except Exception as e:
        log(f"Unexpected error when terminating process {pid}: {e}")


def main(blacklisted_processes: list[str], dev_mode, mom_queue=None) -> None:
    if dev_mode == "1":
        return
    log(
        "Blacklist process started with blacklisted processes: "
        + ", ".join(blacklisted_processes)
    )
    while True:
        find_and_kill_blacklisted_process(blacklisted_processes, mom_queue)
        time.sleep(10)


if __name__ == "__main__":
    main()
