import win32api


def main():
    win32api.MessageBox(0, "Hello, World!", "Greetings", 0x00001000)
    a = win32api.GetUserName()
    print(a)
