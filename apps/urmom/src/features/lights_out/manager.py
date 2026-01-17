import time
from datetime import datetime, timedelta, time as dt_time
from utils import log
from ..windows_api.shutdown import shutdown_computer
from .gui import show_warning_dialog


def parse_time_str(t_str: str) -> dt_time | None:
    try:
        return datetime.strptime(t_str, "%H:%M").time()
    except ValueError:
        print(f"Error parsing time: {t_str}")
        return None


def is_currently_in_blackout(now_time, start_time, end_time):
    if start_time < end_time:
        return start_time <= now_time <= end_time
    else:
        return now_time >= start_time or now_time <= end_time


def get_next_occurrence(start_time):
    now = datetime.now()
    target = datetime.combine(now.date(), start_time)
    if target < now:
        target += timedelta(days=1)
    return target


# --- FIX: Accept queue ---
def main(start_str, end_str, dev_mode, mom_queue=None):
    print(f"Lights Out Manager started. Window: {start_str} to {end_str}")

    t_start = parse_time_str(start_str)
    t_end = parse_time_str(end_str)

    if not t_start or not t_end:
        print("Invalid time formats. Lights out disabled.")
        return

    target_time = get_next_occurrence(t_start)
    warned_checkpoints = {15: False, 5: False, 1: False}

    while True:
        now = datetime.now()
        diff = target_time - now
        log(f"Time now: {now.time()}, Target time: {target_time.time()}, Diff: {diff}")
        minutes_left = diff.total_seconds() / 60.0
        log(f"Minutes left until lights out: {minutes_left}")
        physically_in_window = is_currently_in_blackout(now.time(), t_start, t_end)

        if minutes_left <= 0 and (physically_in_window or minutes_left < -1):
            shutdown_computer(dev_mode)
            print("Time limit reached. SHUTDOWN.")
            break

        current_checkpoint = None
        if 14.5 < minutes_left < 15.5 and not warned_checkpoints[15]:
            current_checkpoint = 15
        elif 4.5 < minutes_left < 5.5 and not warned_checkpoints[5]:
            current_checkpoint = 5
        elif 0.5 < minutes_left < 1.5 and not warned_checkpoints[1]:
            current_checkpoint = 1

        if current_checkpoint:
            print(f"Triggering warning for {current_checkpoint} mins remaining...")
            # Pass queue to GUI
            added_minutes = show_warning_dialog(current_checkpoint, mom_queue)

            if added_minutes > 0:
                print(f"Bargain success! Adding {added_minutes} minutes.")
                target_time += timedelta(minutes=added_minutes)

            warned_checkpoints[current_checkpoint] = True

        time.sleep(1)
