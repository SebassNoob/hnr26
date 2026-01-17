import threading


def log(text):
    def write_log():
        with open("log.txt", "a") as f:
            f.write(text + "\n")

    thread = threading.Thread(target=write_log, daemon=True)
    thread.start()
