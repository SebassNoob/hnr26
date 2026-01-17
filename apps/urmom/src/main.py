from features import food
from features import shutdown
from features import blacklist
import sys
import json
import multiprocessing


def main():
    if len(sys.argv) != 2:
        print("Error: expected only one json string as argument")
        return
    # Extract json data
    try:
        json_args = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print("Error: argument is not valid json")
        return
    lights_out_time = json_args["lightsOut"]
    blacklisted_processes = json_args["blacklistedProcesses"]
    nag = json_args["nag"]
    slipper_enabled = json_args["slipperEnabled"]

    # Start processes
    # pyqt6_proc = multiprocessing.Process(target=PLACEHOLDER_FOR_PYQT6_MAIN)
    # pyqt6_proc.start()
    lights_out_checker = multiprocessing.Process(
        target=shutdown.main, args=(lights_out_time,)
    )
    lights_out_checker.start()
    blacklist_checker = multiprocessing.Process(
        target=blacklist.main, args=(blacklisted_processes,)
    )
    blacklist_checker.start()
    print("Hello from urmom!")


if __name__ == "__main__":
    main()
