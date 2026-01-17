import win32api
import win32security
import datetime
import time
from utils import log


"""
def check_for_lights_out(lights_out_time):
    current_time = datetime.datetime.now().time()
    lights_out_time = datetime.datetime.strptime(lights_out_time.strip("T"), "%H:%M:%S").time()
    log(f"Current time: {current_time}, Lights out time: {lights_out_time}")
    return current_time >= lights_out_time
"""


def shutdown_computer(dev_mode):
    if dev_mode == "1":
        log("Dev mode enabled, skipping shutdown")
        return True

    shutdown_message = "EH WHAT TIME ALREADY? GO TO SLEEP LA TOMORROW YOU CANNOT WAKE UP HOW. I GIVE YOU 30 SECONDS"

    try:
        # Check permissions
        flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)

        privilege_id = win32security.LookupPrivilegeValue(
            None, win32security.SE_SHUTDOWN_NAME
        )

        # Set permission to shutdown
        win32security.AdjustTokenPrivileges(
            token, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
        )

        # Shutdown
        win32api.InitiateSystemShutdown(None, shutdown_message, 30, False, False)
        log("Shutdown initiated successfully")
        return True

    except win32api.error as e:
        error_msg = f"Win32 API error during shutdown: {e}"
        log(error_msg)
        print(error_msg)
        return False

    except win32security.error as e:
        error_msg = f"Win32 Security error during shutdown: {e}"
        log(error_msg)
        print(error_msg)
        return False

    except Exception as e:
        error_msg = f"Unexpected error during shutdown: {e}"
        log(error_msg)
        print(error_msg)
        return False


def main(lights_out_time, dev_mode):
    pass
    """
    log("Shutdown process started with lights out time: " + lights_out_time)
    while True:
        if check_for_lights_out(lights_out_time):
            if dev_mode !='1':
                shutdown_computer()
        time.sleep(60)
    """


if __name__ == "__main__":
    main()
