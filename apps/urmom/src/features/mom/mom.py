import os
import random
import win32api
import win32con
import win32gui
from PIL import Image, ImageWin

from . import popup_window
from . import bubble_window
from . import timer_loop


TRANSPARENT_COLOR = 0x00FF00FF  # BGR magenta (R=255, B=255)
IMAGE_FILENAME = "mom.png"
ICON_FILENAME = "mom.ico"
MOM_SCALE = 1.4
POPUP_INTERVAL_MS = 5000 * 60 * 3
TRAY_ICON_UID = 1
TRAY_CALLBACK_MSG = win32con.WM_USER + 1
TRAY_EXIT_ID = 2001
SCREEN_EDGE_MARGIN = 16
_last_popup_pos = None
_mom_image = None
_main_rect = None
_running = True
_mouse_down_pos = None
_dragging = False

def log(text):
    with open("log.txt", "a") as f:
        f.write(text + "\n")

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


def _add_tray_icon(hwnd):
    script_dir = os.path.dirname(__file__)
    icon_path = os.path.join(script_dir, ICON_FILENAME)
    if os.path.exists(icon_path):
        try:
            icon = win32gui.LoadImage(
                0,
                icon_path,
                win32con.IMAGE_ICON,
                0,
                0,
                win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE,
            )
        except win32gui.error:
            icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
    else:
        icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
    win32gui.Shell_NotifyIcon(
        win32gui.NIM_ADD,
        (
            hwnd,
            TRAY_ICON_UID,
            win32gui.NIF_MESSAGE | win32gui.NIF_ICON | win32gui.NIF_TIP,
            TRAY_CALLBACK_MSG,
            icon,
            "UrMom",
        ),
    )


def _remove_tray_icon(hwnd):
    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, TRAY_ICON_UID))


def _show_tray_menu(hwnd):
    menu = win32gui.CreatePopupMenu()
    win32gui.AppendMenu(menu, win32con.MF_STRING, TRAY_EXIT_ID, "Exit")
    win32gui.SetForegroundWindow(hwnd)
    x, y = win32gui.GetCursorPos()
    win32gui.TrackPopupMenu(
        menu,
        win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
        x,
        y,
        0,
        hwnd,
        None,
    )
    win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)


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

        # 3. Paste only fully-opaque pixels to avoid magenta fringes at edges.
        alpha = src_img.split()[3]
        opaque_mask = alpha.point(lambda a: 255 if a == 255 else 0)
        bg.paste(src_img, (0, 0), opaque_mask)

        if MOM_SCALE != 1.0:
            new_size = (
                int(bg.width * MOM_SCALE),
                int(bg.height * MOM_SCALE),
            )
            bg = bg.resize(new_size, Image.Resampling.LANCZOS)
        _mom_image = bg
    else:
        # Fallback if image missing: create a small red box
        _mom_image = Image.new("RGB", (100, 100), (255, 0, 0))
        print(f"Warning: {IMAGE_FILENAME} not found in {script_dir}")

    class_name = "TransparentTextWindow"

    def wnd_proc(hwnd, msg, wparam, lparam):
        global _main_rect, _running

        def _start_drag_if_needed():
            global _dragging
            _dragging = True
            win32gui.ReleaseCapture()
            win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, 0)

        def _show_bubble():
            bubble_window.advance_phrase()
            bubble_w, bubble_h = bubble_window.get_bubble_size()
            screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            if _main_rect and _mom_image:
                head_x = _main_rect[0] + (_mom_image.width // 2)
                head_y = _main_rect[1] + 20
                bx = head_x - (bubble_w // 2)
                by = head_y - bubble_h - 10
            else:
                bx, by = _random_popup_position(bubble_w, bubble_h, _main_rect)
                head_x = bx + (bubble_w // 2)
            bx = max(
                SCREEN_EDGE_MARGIN, min(bx, screen_w - bubble_w - SCREEN_EDGE_MARGIN)
            )
            by = max(
                SCREEN_EDGE_MARGIN, min(by, screen_h - bubble_h - SCREEN_EDGE_MARGIN)
            )
            tail_center_x = head_x - bx if _main_rect and _mom_image else None
            bubble_window.create_bubble(
                hinstance, bx, by, TRANSPARENT_COLOR, tail_center_x=tail_center_x
            )

        if msg == win32con.WM_PAINT:
            _paint(hwnd)
            return 0
        if msg == TRAY_CALLBACK_MSG:
            if lparam == win32con.WM_RBUTTONUP:
                _show_tray_menu(hwnd)
            return 0
        if msg == win32con.WM_MOVE:
            _main_rect = win32gui.GetWindowRect(hwnd)
            if _mom_image:
                bubble_w, bubble_h = bubble_window.get_bubble_size()
                screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                head_x = _main_rect[0] + (_mom_image.width // 2)
                head_y = _main_rect[1] + 20
                bx = head_x - (bubble_w // 2)
                by = head_y - bubble_h - 10
                bx = max(
                    SCREEN_EDGE_MARGIN,
                    min(bx, screen_w - bubble_w - SCREEN_EDGE_MARGIN),
                )
                by = max(
                    SCREEN_EDGE_MARGIN,
                    min(by, screen_h - bubble_h - SCREEN_EDGE_MARGIN),
                )
                tail_center_x = head_x - bx
                bubble_window.move_bubble(bx, by, tail_center_x=tail_center_x)
            return 0
        if msg == win32con.WM_LBUTTONDOWN:
            global _mouse_down_pos, _dragging
            _mouse_down_pos = (win32api.LOWORD(lparam), win32api.HIWORD(lparam))
            _dragging = False
            win32gui.SetCapture(hwnd)
            return 0
        if msg == win32con.WM_MOUSEMOVE:
            if wparam & win32con.MK_LBUTTON and _mouse_down_pos and not _dragging:
                x = win32api.LOWORD(lparam)
                y = win32api.HIWORD(lparam)
                dx = abs(x - _mouse_down_pos[0])
                dy = abs(y - _mouse_down_pos[1])
                if dx > 3 or dy > 3:
                    _start_drag_if_needed()
            return 0
        if msg == win32con.WM_LBUTTONUP:
            if _mouse_down_pos:
                win32gui.ReleaseCapture()
                if not _dragging:
                    _show_bubble()
                _mouse_down_pos = None
            return 0
        if msg == win32con.WM_RBUTTONDOWN:
            win32gui.DestroyWindow(hwnd)
            return 0
        if msg == win32con.WM_KEYDOWN and wparam == win32con.VK_ESCAPE:
            win32gui.DestroyWindow(hwnd)
            return 0
        if msg == win32con.WM_COMMAND:
            if wparam == TRAY_EXIT_ID:
                win32gui.DestroyWindow(hwnd)
                return 0
        if msg == win32con.WM_DESTROY:
            _remove_tray_icon(hwnd)
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

    width = img_w
    height = img_h

    ex_style = (
        win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
    )
    style = win32con.WS_POPUP
    x = win32api.GetSystemMetrics(win32con.SM_CXSCREEN) - width - 20
    y = win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - height - 20

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

    win32gui.SetLayeredWindowAttributes(
        hwnd, TRANSPARENT_COLOR, 0, win32con.LWA_COLORKEY
    )
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    win32gui.UpdateWindow(hwnd)
    _main_rect = win32gui.GetWindowRect(hwnd)
    _add_tray_icon(hwnd)

    _running = True

    def on_timer_tick():
        popup_w, popup_h = popup_window.get_popup_size()
        px, py = _random_popup_position(popup_w, popup_h, _main_rect)
        popup_window.create_popup(hinstance, px, py, TRANSPARENT_COLOR)

    timer_loop.run_timer_loop(POPUP_INTERVAL_MS, on_timer_tick, lambda: _running)
