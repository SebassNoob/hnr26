from features import mom as mom
from features import shutdown
from features import blacklist
from features import bargain
from features import lights_out
import sys
import os
import json
import multiprocessing

def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")

def main():
    multiprocessing.freeze_support()
    if len(sys.argv) != 2:
        log("Error: expected only one json string as argument")
        log(str(sys.argv))
        return

    # Check for dev mode
    dev_mode = None
    if hasattr(sys, "_MEIPASS"):
        marker_path = os.path.join(sys._MEIPASS, "dev_mode.txt")
        dev_mode = "1" if os.path.exists(marker_path) else "0"
    else:
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
    
    # --- FIX: IPC Queue ---
    # Create a queue for sending commands to the Mom process
    mom_command_queue = multiprocessing.Queue()
    # ----------------------

    log(f"Parsed arguments: lights_out_start={lights_out_start}, lights_out_end={lights_out_end}")

    # Start processes
    blacklist_checker = multiprocessing.Process(
        target=blacklist.main, args=(blacklisted_processes, dev_mode)
    )
    blacklist_checker.start()

    if lights_out_start and lights_out_end:
        lights_out_proc = multiprocessing.Process(
            target=lights_out.main, 
            # Pass the queue to lights_out so it can talk to Mom
            args=(lights_out_start, lights_out_end, mom_command_queue) 
        )
        lights_out_proc.start()

    # Run Mom in the main process (blocking), passing the queue
    mom.main(mom_command_queue)
    print("Hello from urmom!")

if __name__ == "__main__":
    main()