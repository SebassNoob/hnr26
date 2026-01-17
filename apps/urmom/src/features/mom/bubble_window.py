import win32api
import win32con
import win32gui


BUBBLE_PHRASES = [
    "Have you eaten yet?",
    "Drink some water.",
    "Take a short stretch break.",
    "Did you charge your laptop?",
    "Posture check.",
    "Are you still focused?",
    "Stand up for a minute.",
    "Plan your next task.",
    "Take a deep breath.",
    "Be kind to yourself.",
]
_phrase_index = 0
BUBBLE_TEXT = BUBBLE_PHRASES[_phrase_index]
BUBBLE_FONT = "Consolas"
BUBBLE_FONT_HEIGHT = 24
BUBBLE_FONT_WEIGHT = win32con.FW_BOLD
BUBBLE_PAD_X = 14
BUBBLE_PAD_Y = 12
BUBBLE_MAX_WIDTH = 260
TAIL_WIDTH = 18
TAIL_HEIGHT = 12
TAIL_OFFSET_X = 28
BUBBLE_BG = (255, 255, 255)
BUBBLE_BORDER = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)
_transparent_color = None
_current_hwnd = None
_tail_center_x = None


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
        _, line_h = win32gui.GetTextExtentPoint32(hdc, "Ag")
        max_width = BUBBLE_MAX_WIDTH
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph:
                lines.append("")
                continue
            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else f"{current} {word}"
                cand_w, _ = win32gui.GetTextExtentPoint32(hdc, candidate)
                if cand_w <= max_width or not current:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        text_h = max(len(lines), 1) * line_h
        text_w = 0
        for line in lines:
            line_w, _ = win32gui.GetTextExtentPoint32(hdc, line)
            text_w = max(text_w, line_w)
        return min(text_w, max_width), text_h
    finally:
        win32gui.SelectObject(hdc, old_font)
        win32gui.DeleteObject(font)
        win32gui.ReleaseDC(0, hdc)


def get_bubble_size():
    text_w, text_h = _measure_text(
        BUBBLE_TEXT, BUBBLE_FONT_HEIGHT, BUBBLE_FONT_WEIGHT, BUBBLE_FONT
    )
    size_w = text_w + (BUBBLE_PAD_X * 2)
    size_h = text_h + (BUBBLE_PAD_Y * 2) + TAIL_HEIGHT
    return size_w, size_h


def _paint_bubble(hwnd):
    hdc, ps = win32gui.BeginPaint(hwnd)
    try:
        rect = win32gui.GetClientRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        bubble_bottom = height - TAIL_HEIGHT

        if _transparent_color is not None:
            bg_brush = win32gui.CreateSolidBrush(_transparent_color)
            win32gui.FillRect(hdc, rect, bg_brush)
            win32gui.DeleteObject(bg_brush)

        pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(*BUBBLE_BORDER))
        brush = win32gui.CreateSolidBrush(win32api.RGB(*BUBBLE_BG))
        old_pen = win32gui.SelectObject(hdc, pen)
        old_brush = win32gui.SelectObject(hdc, brush)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        win32gui.SetTextColor(hdc, win32api.RGB(*TEXT_COLOR))
        font = win32gui.CreateFontIndirect(
            _create_logfont(BUBBLE_FONT_HEIGHT, BUBBLE_FONT_WEIGHT, BUBBLE_FONT)
        )
        old_font = win32gui.SelectObject(hdc, font)
        try:
            win32gui.RoundRect(hdc, 0, 0, width, bubble_bottom, 12, 12)
            if _tail_center_x is not None:
                tail_left = max(
                    0, min(width - TAIL_WIDTH, _tail_center_x - (TAIL_WIDTH // 2))
                )
            else:
                tail_left = TAIL_OFFSET_X
            tail_right = tail_left + TAIL_WIDTH
            tail_tip = tail_left + (TAIL_WIDTH // 2)
            win32gui.Polygon(
                hdc,
                [
                    (tail_left, bubble_bottom - 1),
                    (tail_right, bubble_bottom - 1),
                    (tail_tip, height),
                ],
            )
            win32gui.DrawText(
                hdc,
                BUBBLE_TEXT,
                -1,
                (
                    BUBBLE_PAD_X,
                    BUBBLE_PAD_Y,
                    width - BUBBLE_PAD_X,
                    bubble_bottom - BUBBLE_PAD_Y,
                ),
                win32con.DT_WORDBREAK | win32con.DT_LEFT,
            )
        finally:
            win32gui.SelectObject(hdc, old_font)
            win32gui.DeleteObject(font)
            win32gui.SelectObject(hdc, old_brush)
            win32gui.SelectObject(hdc, old_pen)
            win32gui.DeleteObject(brush)
            win32gui.DeleteObject(pen)
    finally:
        win32gui.EndPaint(hwnd, ps)


def create_bubble(hinstance, x, y, transparent_color, tail_center_x=None):
    global _transparent_color, _tail_center_x
    _transparent_color = transparent_color
    _tail_center_x = tail_center_x
    class_name = "MomBubbleWindow"
    global _current_hwnd
    if _current_hwnd:
        try:
            win32gui.DestroyWindow(_current_hwnd)
        except win32gui.error:
            pass
        _current_hwnd = None

    def bubble_proc(hwnd, msg, wparam, lparam):
        global _current_hwnd
        if msg == win32con.WM_PAINT:
            _paint_bubble(hwnd)
            return 0
        if msg == win32con.WM_LBUTTONDOWN:
            win32gui.DestroyWindow(hwnd)
            return 0
        if msg == win32con.WM_DESTROY:
            if _current_hwnd == hwnd:
                _current_hwnd = None
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    wnd_class = win32gui.WNDCLASS()
    wnd_class.hInstance = hinstance
    wnd_class.lpszClassName = class_name
    wnd_class.lpfnWndProc = bubble_proc
    wnd_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wnd_class.hbrBackground = win32gui.CreateSolidBrush(transparent_color)
    try:
        win32gui.RegisterClass(wnd_class)
    except win32gui.error:
        pass

    size_w, size_h = get_bubble_size()
    hwnd_bubble = win32gui.CreateWindowEx(
        win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
        class_name,
        "MomBubble",
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
        hwnd_bubble, transparent_color, 0, win32con.LWA_COLORKEY
    )
    win32gui.ShowWindow(hwnd_bubble, win32con.SW_SHOWNORMAL)
    win32gui.UpdateWindow(hwnd_bubble)
    _current_hwnd = hwnd_bubble


def advance_phrase():
    global _phrase_index, BUBBLE_TEXT
    _phrase_index = (_phrase_index + 1) % len(BUBBLE_PHRASES)
    BUBBLE_TEXT = BUBBLE_PHRASES[_phrase_index]


def move_bubble(x, y, tail_center_x=None):
    global _tail_center_x
    if not _current_hwnd:
        return
    tail_changed = tail_center_x is not None and tail_center_x != _tail_center_x
    _tail_center_x = tail_center_x
    win32gui.SetWindowPos(
        _current_hwnd,
        0,
        x,
        y,
        0,
        0,
        win32con.SWP_NOZORDER
        | win32con.SWP_NOSIZE
        | win32con.SWP_NOACTIVATE
        | win32con.SWP_NOREDRAW,
    )
    if tail_changed:
        win32gui.InvalidateRect(_current_hwnd, None, True)
        win32gui.UpdateWindow(_current_hwnd)
