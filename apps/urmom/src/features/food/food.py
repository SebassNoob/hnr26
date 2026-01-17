import os
import random
import win32api
import win32con
import win32gui
from PIL import Image, ImageWin

from . import popup_window
from . import timer_loop


TRANSPARENT_COLOR = 0x00FF00FF  # BGR magenta (R=255, B=255)
IMAGE_FILENAME = "mom.png"
BUTTON_ID = 1001
POPUP_INTERVAL_MS = 5000
BUTTON_WIDTH = 70
BUTTON_HEIGHT = 28
BUTTON_PAD_Y = 8
_last_popup_pos = None
_mom_image = None
_main_rect = None
_running = True


def _paint(hwnd):
    hdc, ps = win32gui.BeginPaint(hwnd)
    try:
        if _mom_image:
            # Create a Device Independent Bitmap (DIB) from the loaded image
            dib = ImageWin.Dib(_mom_image)
            # Draw the image at 0,0
            dib.draw(hdc, (0, 0, _mom_image.width, _mom_image.height))
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
    global _mom_image, _main_rect, _running
    
    # Load image before creating window
    script_dir = os.path.dirname(__file__)
    image_path = os.path.join(script_dir, IMAGE_FILENAME)
    
    if os.path.exists(image_path):
        # 1. Open image and ensure it has Alpha channel
        src_img = Image.open(image_path).convert("RGBA")
        
        # 2. Create a solid background with the transparent color (Magenta)
        #    PIL RGB for Magenta is (255, 0, 255)
        bg = Image.new("RGB", src_img.size, (255, 0, 255))
        
        # 3. Paste the PNG onto the Magenta background using the alpha channel as a mask
        #    This fills transparent areas with Magenta, which Windows will then remove.
        bg.paste(src_img, (0, 0), src_img)
        
        _mom_image = bg
    else:
        # Fallback if image missing: create a small red box
        _mom_image = Image.new("RGB", (100, 100), (255, 0, 0))
        print(f"Warning: {IMAGE_FILENAME} not found in {script_dir}")

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

    # Calculate dimensions based on image size
    img_w, img_h = _mom_image.size
    
    width = max(img_w, BUTTON_WIDTH)
    height = img_h + BUTTON_HEIGHT + BUTTON_PAD_Y
    
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
    button_y = img_h + (BUTTON_PAD_Y // 2)
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