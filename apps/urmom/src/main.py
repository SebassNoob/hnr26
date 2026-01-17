from features import mom
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
    # Check if dev mode is enabled
    dev_mode = None
    if hasattr(sys, '_MEIPASS'):  # Running from PyInstaller bundle
        marker_path = os.path.join(sys._MEIPASS, 'dev_mode.txt')
        dev_mode = '1' if os.path.exists(marker_path) else '0'
    else:  # Running directly (e.g., in development)
        dev_mode = os.environ.get('dev', '0')
    
    if dev_mode == '1':
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
    log(f"Parsed arguments: lights_out_time={lights_out_time}, blacklisted_processes={blacklisted_processes}, nag={nag}, slipper_enabled={slipper_enabled}")
    # Start processes
    # pyqt6_proc = multiprocessing.Process(target=PLACEHOLDER_FOR_PYQT6_MAIN)
    # pyqt6_proc.start()
    # lights_out_checker = multiprocessing.Process(
    #     target=shutdown.main, args=(lights_out_time,)
    # )
    # lights_out_checker.start()
    # blacklist_checker = multiprocessing.Process(
    #     target=blacklist.main, args=(blacklisted_processes,)
    # )
    # blacklist_checker.start()

    lights_out_proc = multiprocessing.Process(
        target=lights_out.main, args=(lights_out_time,)
    )
    lights_out_proc.start()
    mom.main()
    print("Hello from urmom!")


if __name__ == "__main__":
    main()
