import win32api
import win32con
import win32gui


POPUP_TEXT = "🥛"
POPUP_FONT = "Consolas"
POPUP_FONT_HEIGHT = 48
POPUP_FONT_WEIGHT = win32con.FW_BOLD
POPUP_PAD_X = 12
POPUP_PAD_Y = 10


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


def get_popup_size():
    text_w, text_h = _measure_text(
        POPUP_TEXT, POPUP_FONT_HEIGHT, POPUP_FONT_WEIGHT, POPUP_FONT
    )
    size_w = text_w + (POPUP_PAD_X * 2)
    size_h = text_h + (POPUP_PAD_Y * 2)
    return size_w, size_h


def _paint_popup(hwnd):
    hdc, ps = win32gui.BeginPaint(hwnd)
    try:
        rect = win32gui.GetClientRect(hwnd)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        win32gui.SetTextColor(hdc, win32api.RGB(0, 0, 0))
        font = win32gui.CreateFontIndirect(
            _create_logfont(POPUP_FONT_HEIGHT, POPUP_FONT_WEIGHT, POPUP_FONT)
        )
        old_font = win32gui.SelectObject(hdc, font)
        try:
            win32gui.DrawText(
                hdc,
                POPUP_TEXT,
                -1,
                rect,
                win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE,
            )
        finally:
            win32gui.SelectObject(hdc, old_font)
            win32gui.DeleteObject(font)
    finally:
        win32gui.EndPaint(hwnd, ps)


def create_popup(hinstance, x, y, transparent_color):
    class_name = "HiPopupWindow"

    def popup_proc(hwnd, msg, wparam, lparam):
        if msg == win32con.WM_PAINT:
            _paint_popup(hwnd)
            return 0
        if msg == win32con.WM_LBUTTONDOWN:
            win32gui.DestroyWindow(hwnd)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wnd_class = win32gui.WNDCLASS()
    wnd_class.hInstance = hinstance
    wnd_class.lpszClassName = class_name
    wnd_class.lpfnWndProc = popup_proc
    wnd_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wnd_class.hbrBackground = win32gui.CreateSolidBrush(transparent_color)
    try:
        win32gui.RegisterClass(wnd_class)
    except win32gui.error:
        pass

    size_w, size_h = get_popup_size()
    hwnd_popup = win32gui.CreateWindowEx(
        win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
        class_name,
        "Hi",
        win32con.WS_POPUP,
        x,
        y,
        size_w,
        size_h,
        0,
        0,
        hinstance,
        None,
    )
    win32gui.SetLayeredWindowAttributes(
        hwnd_popup, transparent_color, 0, win32con.LWA_COLORKEY
    )
    win32gui.ShowWindow(hwnd_popup, win32con.SW_SHOWNORMAL)
    win32gui.UpdateWindow(hwnd_popup)
