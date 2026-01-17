from features import mom_2 as mom
from features import blacklist
from features import bargain
from features import lights_out
import sys
import os
import json
import multiprocessing
import threading
from utils import tray

def cleanup_generator(procs):
    def cleanup():
        print("Shutting down everything...")
        for p in procs:
            if p.is_alive():
                p.terminate() # Graceful request
                p.join()      # Wait for it to actually stop
        sys.exit(0)
    return cleanup


def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")

def main():
    multiprocessing.freeze_support()
    if len(sys.argv) != 2:
        log("Error: expected only one json string as argument")
        log(str(sys.argv))
        return
    # Check if dev mode is enabled
    dev_mode = None
    if hasattr(sys, "_MEIPASS"):  # Running from PyInstaller bundle
        marker_path = os.path.join(sys._MEIPASS, "dev_mode.txt")
        dev_mode = "1" if os.path.exists(marker_path) else "0"
    else:  # Running directly (e.g., in development)
        dev_mode = os.environ.get("dev", "0")

    if dev_mode == "1":
        log("Running in dev mode")
    else:
        log("Running in production mode")
    # Extract json data
    try:
        json_args = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        log("Error: argument is not valid json")
        return
    lights_out_start = json_args["lightsOutStart"]
    lights_out_end = json_args["lightsOutEnd"]
    blacklisted_processes = json_args["blacklistedProcesses"]
    nag = json_args["nag"]
    slipper_enabled = json_args["slipperEnabled"]
    log(
        f"Parsed arguments: lights_out_start={lights_out_start}, lights_out_end={lights_out_end}, blacklisted={blacklisted_processes}"
    )
    # Start processes
    procs = []
    blacklist_checker = multiprocessing.Process(
        target=blacklist.main, args=(blacklisted_processes, dev_mode)
    )
    if lights_out_start and lights_out_end:
        lights_out_proc = multiprocessing.Process(
            target=lights_out.main, args=(lights_out_start, lights_out_end)
        )
    mom_proc = multiprocessing.Process(
        target=mom.main, args=()
    )
    procs.extend([blacklist_checker, lights_out_proc, mom_proc])
    for p in procs:
        p.start()
    print("Hello from urmom!")

    # Create and run the tray icon in a separate thread
    icon = tray.create_icon(cleanup_generator(procs))
    icon_thread = threading.Thread(target=icon.run)
    icon_thread.start()



if __name__ == "__main__":
    main()
