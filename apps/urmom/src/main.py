from features import food
from features import shutdown
import sys
import json

def main():
    if len(sys.argv) != 2:
        print("Error: expected only one json string as argument")
        return
    try:
        json_args = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print("Error: argument is not valid json")
        return
    lights_out_time = json_args["lightsOut"]
    blacklisted_processes = json_args["blacklistedProcesses"]
    nag = json_args["nag"]
    slipper_enabled = json_args["slipperEnabled"]
    shutdown.main()
    print("Hello from urmom!")


if __name__ == "__main__":
    main()
