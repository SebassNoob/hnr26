from datetime import datetime

import win32api
import win32con
import win32gui


WINDOW_CLASS = "TodoWindow"
WINDOW_TITLE = "Todo"
FONT_NAME = "Consolas"
FONT_SIZE = 18

ID_INPUT = 1001
ID_ADD = 1002
ID_DELETE = 1003
ID_LIST = 1004
ID_PRIORITY = 1005
ID_DEADLINE = 1006
ID_SORT = 1007

PRIORITIES = ["Low", "Medium", "High"]
SORT_OPTIONS = ["Created", "Priority", "Deadline", "Priority then deadline"]


def _create_font():
    logfont = win32gui.LOGFONT()
    logfont.lfHeight = FONT_SIZE
    logfont.lfWeight = win32con.FW_NORMAL
    logfont.lfCharSet = win32con.DEFAULT_CHARSET
    logfont.lfOutPrecision = win32con.OUT_DEFAULT_PRECIS
    logfont.lfClipPrecision = win32con.CLIP_DEFAULT_PRECIS
    logfont.lfQuality = win32con.DEFAULT_QUALITY
    logfont.lfPitchAndFamily = win32con.DEFAULT_PITCH | win32con.FF_DONTCARE
    logfont.lfFaceName = FONT_NAME
    return win32gui.CreateFontIndirect(logfont)


def main():
    hinstance = win32api.GetModuleHandle(None)
    font = _create_font()
    tasks = []
    display_order = []
    next_id = 1

    def _combo_text(hwnd_combo):
        index = win32gui.SendMessage(hwnd_combo, win32con.CB_GETCURSEL, 0, 0)
        if index == win32con.CB_ERR:
            return ""
        buffer = win32gui.PyMakeBuffer(64)
        win32gui.SendMessage(hwnd_combo, win32con.CB_GETLBTEXT, index, buffer)
        return buffer[:].tobytes().decode(errors="ignore")

    def _parse_deadline(text):
        text = text.strip()
        if not text:
            return None, True
        try:
            return datetime.strptime(text, "%Y-%m-%d").date(), True
        except ValueError:
            win32api.MessageBox(
                0,
                "Deadline must be in YYYY-MM-DD format.",
                "Invalid deadline",
                win32con.MB_ICONWARNING,
            )
            return None, False

    def _priority_rank(value):
        return {"High": 0, "Medium": 1, "Low": 2}.get(value, 3)

    def _format_task(task):
        deadline = task["deadline"].isoformat() if task["deadline"] else "None"
        return f"[{task['priority']}] [{deadline}] {task['text']}"

    def _refresh_list():
        nonlocal display_order
        sort_mode = _combo_text(sort_hwnd) or "Created"
        if sort_mode == "Priority":
            ordered = sorted(tasks, key=lambda t: _priority_rank(t["priority"]))
        elif sort_mode == "Deadline":
            ordered = sorted(
                tasks,
                key=lambda t: t["deadline"] or datetime.max.date(),
            )
        elif sort_mode == "Priority then deadline":
            ordered = sorted(
                tasks,
                key=lambda t: (
                    _priority_rank(t["priority"]),
                    t["deadline"] or datetime.max.date(),
                ),
            )
        else:
            ordered = list(tasks)

        display_order = [task["id"] for task in ordered]
        win32gui.SendMessage(list_hwnd, win32con.LB_RESETCONTENT, 0, 0)
        for task in ordered:
            win32gui.SendMessage(
                list_hwnd, win32con.LB_ADDSTRING, 0, _format_task(task)
            )

    def wnd_proc(hwnd, msg, wparam, lparam):
        if msg == win32con.WM_COMMAND:
            if win32api.HIWORD(wparam) == win32con.CBN_SELCHANGE:
                if win32api.LOWORD(wparam) == ID_SORT:
                    _refresh_list()
                    return 0
            if win32api.HIWORD(wparam) == win32con.BN_CLICKED:
                if win32api.LOWORD(wparam) == ID_ADD:
                    nonlocal next_id
                    text = win32gui.GetWindowText(input_hwnd).strip()
                    deadline, ok = _parse_deadline(
                        win32gui.GetWindowText(deadline_hwnd)
                    )
                    if not ok:
                        return 0
                    priority = _combo_text(priority_hwnd) or "Medium"
                    if text:
                        tasks.append(
                            {
                                "id": next_id,
                                "text": text,
                                "priority": priority,
                                "deadline": deadline,
                            }
                        )
                        next_id += 1
                        _refresh_list()
                        win32gui.SetWindowText(input_hwnd, "")
                    return 0
                if win32api.LOWORD(wparam) == ID_DELETE:
                    index = win32gui.SendMessage(
                        list_hwnd, win32con.LB_GETCURSEL, 0, 0
                    )
                    if index != win32con.LB_ERR:
                        task_id = display_order[index]
                        for i, task in enumerate(tasks):
                            if task["id"] == task_id:
                                del tasks[i]
                                break
                        _refresh_list()
                    return 0
            return 0
        if msg == win32con.WM_DESTROY:
            win32gui.DeleteObject(font)
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wnd_class = win32gui.WNDCLASS()
    wnd_class.hInstance = hinstance
    wnd_class.lpszClassName = WINDOW_CLASS
    wnd_class.lpfnWndProc = wnd_proc
    wnd_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wnd_class.hbrBackground = win32con.COLOR_WINDOW + 1
    try:
        win32gui.RegisterClass(wnd_class)
    except win32gui.error:
        pass

    width, height = 540, 460
    x = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN) - width) // 2
    y = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - height) // 2

    hwnd = win32gui.CreateWindowEx(
        0,
        WINDOW_CLASS,
        WINDOW_TITLE,
        win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_SYSMENU,
        x,
        y,
        width,
        height,
        0,
        0,
        hinstance,
        None,
    )

    win32gui.CreateWindow(
        "STATIC",
        "Task",
        win32con.WS_CHILD | win32con.WS_VISIBLE,
        16,
        18,
        50,
        20,
        hwnd,
        0,
        hinstance,
        None,
    )

    input_hwnd = win32gui.CreateWindowEx(
        0,
        "EDIT",
        "",
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | win32con.WS_BORDER
        | win32con.ES_AUTOHSCROLL,
        70,
        14,
        250,
        26,
        hwnd,
        ID_INPUT,
        hinstance,
        None,
    )

    add_hwnd = win32gui.CreateWindow(
        "BUTTON",
        "Add",
        win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
        334,
        12,
        90,
        30,
        hwnd,
        ID_ADD,
        hinstance,
        None,
    )

    delete_hwnd = win32gui.CreateWindow(
        "BUTTON",
        "Delete",
        win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
        436,
        12,
        90,
        30,
        hwnd,
        ID_DELETE,
        hinstance,
        None,
    )

    win32gui.CreateWindow(
        "STATIC",
        "Priority",
        win32con.WS_CHILD | win32con.WS_VISIBLE,
        16,
        56,
        60,
        20,
        hwnd,
        0,
        hinstance,
        None,
    )

    priority_hwnd = win32gui.CreateWindow(
        "COMBOBOX",
        "",
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | win32con.CBS_DROPDOWNLIST
        | win32con.WS_VSCROLL,
        86,
        52,
        120,
        200,
        hwnd,
        ID_PRIORITY,
        hinstance,
        None,
    )
    for value in PRIORITIES:
        win32gui.SendMessage(priority_hwnd, win32con.CB_ADDSTRING, 0, value)
    win32gui.SendMessage(priority_hwnd, win32con.CB_SETCURSEL, 1, 0)

    win32gui.CreateWindow(
        "STATIC",
        "Deadline (YYYY-MM-DD)",
        win32con.WS_CHILD | win32con.WS_VISIBLE,
        220,
        56,
        160,
        20,
        hwnd,
        0,
        hinstance,
        None,
    )

    deadline_hwnd = win32gui.CreateWindowEx(
        0,
        "EDIT",
        "",
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | win32con.WS_BORDER
        | win32con.ES_AUTOHSCROLL,
        384,
        52,
        140,
        26,
        hwnd,
        ID_DEADLINE,
        hinstance,
        None,
    )

    win32gui.CreateWindow(
        "STATIC",
        "Sort",
        win32con.WS_CHILD | win32con.WS_VISIBLE,
        16,
        92,
        40,
        20,
        hwnd,
        0,
        hinstance,
        None,
    )

    sort_hwnd = win32gui.CreateWindow(
        "COMBOBOX",
        "",
        win32con.WS_CHILD
        | win32con.WS_VISIBLE
        | win32con.CBS_DROPDOWNLIST
        | win32con.WS_VSCROLL,
        86,
        88,
        200,
        200,
        hwnd,
        ID_SORT,
        hinstance,
        None,
    )
    for value in SORT_OPTIONS:
        win32gui.SendMessage(sort_hwnd, win32con.CB_ADDSTRING, 0, value)
    win32gui.SendMessage(sort_hwnd, win32con.CB_SETCURSEL, 0, 0)

    list_hwnd = win32gui.CreateWindowEx(
        win32con.WS_EX_CLIENTEDGE,
        "LISTBOX",
        "",
        win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.LBS_NOTIFY,
        16,
        124,
        508,
        300,
        hwnd,
        ID_LIST,
        hinstance,
        None,
    )

    for child in (
        input_hwnd,
        add_hwnd,
        delete_hwnd,
        list_hwnd,
        priority_hwnd,
        deadline_hwnd,
        sort_hwnd,
    ):
        win32gui.SendMessage(child, win32con.WM_SETFONT, font, True)

    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    win32gui.UpdateWindow(hwnd)
    win32gui.PumpMessages()
