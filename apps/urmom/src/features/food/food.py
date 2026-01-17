import random
import win32api
import win32con
import win32gui

from . import popup_window
from . import timer_loop


TRANSPARENT_COLOR = 0x00FF00FF  # BGR magenta
TEXT = "👩"
FONT_NAME = "Consolas"
TEXT_FONT_HEIGHT = 36
TEXT_FONT_WEIGHT = win32con.FW_BOLD
TEXT_PAD_X = 12
TEXT_PAD_Y = 10
BUTTON_ID = 1001
POPUP_INTERVAL_MS = 5000
BUTTON_WIDTH = 70
BUTTON_HEIGHT = 28
BUTTON_PAD_Y = 8
_last_popup_pos = None
_text_rect = None
_main_rect = None
_running = True


def _create_logfont(height, weight, face_name):
    logfont = win32gui.LOGFONT()
    logfont.lfHeight = height
    logfont.lfWeight = weight
    logfont.lfCharSet = win32con.DEFAULT_CHARSET
    logfont.lfOutPrecision = win32con.OUT_DEFAULT_PRECIS
    logfont.lfClipPrecision = win32con.CLIP_DEFAULT_PRECIS
    logfont.lfQuality = win32con.DEFAULT_QUALITY
    logfont.lfPitchAndFamily = win32con.DEFAULT_PITCH | win32con.FF_DONTCARE
    logfont.lfFaceName = face_name
    return logfont


def _measure_text(text, height, weight, face_name):
    hdc = win32gui.GetDC(0)
    font = win32gui.CreateFontIndirect(_create_logfont(height, weight, face_name))
    old_font = win32gui.SelectObject(hdc, font)
    try:
        return win32gui.GetTextExtentPoint32(hdc, text)
    finally:
        win32gui.SelectObject(hdc, old_font)
        win32gui.DeleteObject(font)
        win32gui.ReleaseDC(0, hdc)


def _paint(hwnd):
    hdc, ps = win32gui.BeginPaint(hwnd)
    try:
        rect = _text_rect or win32gui.GetClientRect(hwnd)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        win32gui.SetTextColor(hdc, win32api.RGB(0, 0, 0))
        font = win32gui.CreateFontIndirect(
            _create_logfont(TEXT_FONT_HEIGHT, TEXT_FONT_WEIGHT, FONT_NAME)
        )
        old_font = win32gui.SelectObject(hdc, font)
        try:
            win32gui.DrawText(
                hdc,
                TEXT,
                -1,
                rect,
                win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE,
            )
        finally:
            win32gui.SelectObject(hdc, old_font)
            win32gui.DeleteObject(font)
    finally:
        win32gui.EndPaint(hwnd, ps)


def _rects_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def _random_popup_position(width, height, avoid_rect=None):
    global _last_popup_pos
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    max_x = max(0, screen_w - width)
    max_y = max(0, screen_h - height)

    for _ in range(20):
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        if _last_popup_pos == (x, y):
            continue
        if avoid_rect:
            candidate = (x, y, x + width, y + height)
            if _rects_intersect(candidate, avoid_rect):
                continue
        if _last_popup_pos != (x, y):
            _last_popup_pos = (x, y)
            return x, y

    candidates = [(0, 0), (max_x, 0), (0, max_y), (max_x, max_y)]
    for x, y in candidates:
        if _last_popup_pos == (x, y):
            continue
        if avoid_rect:
            candidate = (x, y, x + width, y + height)
            if _rects_intersect(candidate, avoid_rect):
                continue
        _last_popup_pos = (x, y)
        return x, y

    x = 0
    y = 0
    _last_popup_pos = (x, y)
    return x, y


def main():
    global _text_rect, _main_rect, _running
    class_name = "TransparentTextWindow"

    def wnd_proc(hwnd, msg, wparam, lparam):
        global _main_rect, _running
        if msg == win32con.WM_PAINT:
            _paint(hwnd)
            return 0
        if msg == win32con.WM_MOVE:
            _main_rect = win32gui.GetWindowRect(hwnd)
            return 0
        if msg == win32con.WM_LBUTTONDOWN:
            win32gui.ReleaseCapture()
            win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, 0)
            return 0
        if msg == win32con.WM_COMMAND:
            if win32api.HIWORD(wparam) == win32con.BN_CLICKED:
                if win32api.LOWORD(wparam) == BUTTON_ID:
                    popup_w, popup_h = popup_window.get_popup_size()
                    px, py = _random_popup_position(popup_w, popup_h, _main_rect)
                    popup_window.create_popup(hinstance, px, py, TRANSPARENT_COLOR)
                    return 0
        if msg == win32con.WM_RBUTTONDOWN:
            win32gui.DestroyWindow(hwnd)
            return 0
        if msg == win32con.WM_KEYDOWN and wparam == win32con.VK_ESCAPE:
            win32gui.DestroyWindow(hwnd)
            return 0
        if msg == win32con.WM_DESTROY:
            _running = False
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    hinstance = win32api.GetModuleHandle(None)
    wnd_class = win32gui.WNDCLASS()
    wnd_class.hInstance = hinstance
    wnd_class.lpszClassName = class_name
    wnd_class.lpfnWndProc = wnd_proc
    wnd_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wnd_class.hbrBackground = win32gui.CreateSolidBrush(TRANSPARENT_COLOR)
    win32gui.RegisterClass(wnd_class)

    text_w, text_h = _measure_text(TEXT, TEXT_FONT_HEIGHT, TEXT_FONT_WEIGHT, FONT_NAME)
    text_area_w = text_w + (TEXT_PAD_X * 2)
    text_area_h = text_h + (TEXT_PAD_Y * 2)
    width = max(text_area_w, BUTTON_WIDTH + (TEXT_PAD_X * 2))
    height = text_area_h + BUTTON_HEIGHT + BUTTON_PAD_Y
    _text_rect = (0, 0, width, text_area_h)

    ex_style = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
    style = win32con.WS_POPUP
    x = (win32api.GetSystemMetrics(win32con.SM_CXSCREEN) - width) // 2
    y = (win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - height) // 2

    hwnd = win32gui.CreateWindowEx(
        ex_style,
        class_name,
        "Greetings",
        style,
        x,
        y,
        width,
        height,
        0,
        0,
        hinstance,
        None,
    )

    button_x = (width - BUTTON_WIDTH) // 2
    button_y = text_area_h + (BUTTON_PAD_Y // 2)
    win32gui.CreateWindow(
        "BUTTON",
        "Hi",
        win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
        button_x,
        button_y,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
        hwnd,
        BUTTON_ID,
        hinstance,
        None,
    )

    win32gui.SetLayeredWindowAttributes(
        hwnd, TRANSPARENT_COLOR, 0, win32con.LWA_COLORKEY
    )
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    win32gui.UpdateWindow(hwnd)
    _main_rect = win32gui.GetWindowRect(hwnd)

    _running = True

    def on_timer_tick():
        popup_w, popup_h = popup_window.get_popup_size()
        px, py = _random_popup_position(popup_w, popup_h, _main_rect)
        popup_window.create_popup(hinstance, px, py, TRANSPARENT_COLOR)

    timer_loop.run_timer_loop(POPUP_INTERVAL_MS, on_timer_tick, lambda: _running)
