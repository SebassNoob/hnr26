import time
from datetime import datetime, timedelta, time as dt_time
from .gui import show_warning_dialog

def parse_time_str(t_str):
    """
    Parses time strings. Handles formats: "T%H:%M:%S" (ISO-ish) or "%H:%M".
    Returns a datetime.time object.
    """
    # Remove leading 'T' if present (e.g. from Go/JS ISO format)
    if t_str.startswith("T"):
        t_str = t_str[1:]
    
    # Try parsing seconds, then HH:MM
    try:
        return datetime.strptime(t_str, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(t_str, "%H:%M").time()
        except ValueError:
            print(f"Error parsing time: {t_str}")
            return None

def is_currently_in_blackout(now_time, start_time, end_time):
    """
    Checks if now_time is inside the window [start_time, end_time].
    Handles windows that span midnight (e.g. 23:00 to 07:00).
    """
    if start_time < end_time:
        # Standard day window (e.g. 14:00 to 16:00)
        return start_time <= now_time <= end_time
    else:
        # Overnight window (e.g. 22:00 to 06:00)
        # It's blackout if it's after start OR before end
        return now_time >= start_time or now_time <= end_time

def get_next_occurrence(start_time):
    """
    Returns a datetime for the next occurrence of start_time.
    """
    now = datetime.now()
    target = datetime.combine(now.date(), start_time)
    
    # If the time has already passed today, target is tomorrow
    if target < now:
        target += timedelta(days=1)
    
    return target

def main(start_str, end_str):
    print(f"Lights Out Manager started. Window: {start_str} to {end_str}")
    
    t_start = parse_time_str(start_str)
    t_end = parse_time_str(end_str)

    if not t_start or not t_end:
        print("Invalid time formats. Lights out disabled.")
        return

    # Calculate the initial target (shutdown) time
    target_time = get_next_occurrence(t_start)

    # Tracking which warnings we've already shown
    warned_checkpoints = {15: False, 5: False, 1: False}

    while True:
        now = datetime.now()
        
        # 1. Immediate Check: Are we already strictly inside the blackout window?
        # Note: We check raw times to see if we should have been asleep already.
        # However, if we bargained (target_time > now), we respect the bargain 
        # even if raw time says we are in the window.
        
        # Calculate time remaining until the enforced shutdown
        # (This handles the countdown AND the bargaining extensions)
        diff = target_time - now
        minutes_left = diff.total_seconds() / 60.0
        
        # Debug output occasionally
        # print(f"Minutes left: {minutes_left:.2f}")

        # Check if we are physically in the blackout window AND we have run out of time
        # (Handling the case where user starts app inside the window)
        physically_in_window = is_currently_in_blackout(now.time(), t_start, t_end)
        
        # CONDITION: Shutdown
        if minutes_left <= 0:
            if physically_in_window:
                print("In blackout window. SHUTDOWN.")
                break
            else:
                # We reached the count down, but strictly speaking we aren't in the 
                # blackout window yet (e.g., target was set for tomorrow). 
                # This ensures we don't shutdown if target_time is tomorrow.
                # However, minutes_left < 0 implies we passed the target.
                # If target was "Tomorrow 23:00" and now is "Today 22:00", minutes_left is positive.
                # If minutes_left is negative, we passed it.
                print("Time limit reached. SHUTDOWN.")
                break

        # CONDITION: Checkpoints / Warnings
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
                
                # If we added time, we might need to reset checkpoints 
                # if we were pushed back significantly.
                # For now, simplistic approach: don't reset, just let time run out.
            
            warned_checkpoints[current_checkpoint] = True

        time.sleep(1)