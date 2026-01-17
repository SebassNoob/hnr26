import win32api
import win32security
import datetime
import time


def check_for_lights_out(lights_out_time):
    current_time = datetime.datetime.now()
    """
    formatting to be done...
    """
    return current_time >= lights_out_time


def shutdown_computer():
    shutdown_message = "EH WHAT TIME ALREADY? GO TO SLEEP LA TOMORROW YOU CANNOT WAKE UP HOW. I GIVE YOU 10 SECONDS"

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
    win32api.InitiateSystemShutdown(None, shutdown_message, 10, False, False)


def main(lights_out_time):
    while True:
        if check_for_lights_out(lights_out_time):
            shutdown_computer()
        time.sleep(60)


if __name__ == "__main__":
    main()
