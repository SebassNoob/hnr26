import time

import win32gui


def run_timer_loop(interval_ms, on_tick, should_continue):
    interval_s = interval_ms / 1000.0
    next_time = time.time() + interval_s

    while should_continue():
        win32gui.PumpWaitingMessages()

        now = time.time()
        if now >= next_time:
            on_tick()
            next_time = now + interval_s

        time.sleep(0.01)
