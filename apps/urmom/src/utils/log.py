def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")
