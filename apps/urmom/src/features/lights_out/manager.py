import time
from datetime import datetime, timedelta
from .gui import show_warning_dialog


def parse_time(time_str):
    try:
        now = datetime.now()
        t = datetime.strptime(time_str, "T%H:%M:%S").time()
        target = datetime.combine(now.date(), t)

        # If target is already passed today by a significant margin, assume tomorrow
        # (For this simple logic, we just target the next occurrence of this time)
        if target < now:
            target += timedelta(days=1)

        return target
    except ValueError:
        print(f"Error parsing time: {time_str}")
        return None


def main(lights_out_str):
    print(f"Lights Out Manager started for: {lights_out_str}")
    target_time = parse_time(lights_out_str)
    print("now:", datetime.now())
    print("target", target_time)

    if not target_time:
        return

    # Tracking which warnings we've already shown
    warned_checkpoints = {15: False, 5: False, 1: False}

    while True:
        now = datetime.now()
        diff = target_time - now
        minutes_left = diff.total_seconds() / 60.0
        print(minutes_left)

        if minutes_left <= 0:
            print("shutdown")
            break

        # Checkpoints logic
        current_checkpoint = None
        if 14.5 < minutes_left < 15.5 and not warned_checkpoints[15]:
            current_checkpoint = 15
        elif 4.5 < minutes_left < 5.5 and not warned_checkpoints[5]:
            current_checkpoint = 5
        elif 0.5 < minutes_left < 1.5 and not warned_checkpoints[1]:
            current_checkpoint = 1

        if current_checkpoint:
            print(f"Triggering warning for {current_checkpoint} mins remaining...")
            # This blocks execution while user interacts
            added_minutes = show_warning_dialog(current_checkpoint)

            if added_minutes > 0:
                print(f"Bargain success! Adding {added_minutes} minutes.")
                target_time += timedelta(minutes=added_minutes)
                # Reset checkpoints if we were pushed back significantly?
                # For simplicity, just mark this checkpoint as done so we don't spam.

            warned_checkpoints[current_checkpoint] = True

        time.sleep(1)
