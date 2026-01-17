import sys
import os
import random
import queue  # For the Empty exception
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QAction, QIcon, QMouseEvent

from .bubble import BubbleWidget
from .popup import PopupWidget
import signal

# Import SlipperOverlay directly so we can spawn it here
from features.slipper.slipper import SlipperOverlay

from utils.paths import get_asset_path

# Constants
IMAGE_FILENAME = "mom.png"
ICON_FILENAME = "mom.ico"
MOM_SCALE = 1.4
POPUP_INTERVAL_MS = 5000 * 60 * 3
SCREEN_EDGE_MARGIN = 16

_instance = None


def get_mom_instance():
    return _instance


class MomWidget(QWidget):
    def __init__(self, command_queue=None, messages=None):
        super().__init__()
        global _instance
        _instance = self

        self.command_queue = command_queue
        self.messages = messages
        self.original_messages = messages if messages else ["Drink some water.", "Sit up straight."]

        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Initial Load
        self.load_pixmap(IMAGE_FILENAME)

        # Initial Position
        screen_geo = self.screen().geometry()
        start_x = screen_geo.width() - self.width() - 20
        start_y = screen_geo.height() - self.height() - 20
        self.move(start_x, start_y)

        # State
        self.dragging = False
        self.drag_start_position = QPoint()
        self.bubble = None
        self.popups = []

        # System Tray
        script_dir = os.path.dirname(__file__)
        self.init_tray_icon(script_dir)

        # Popup Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.spawn_popup)
        self.timer.start(POPUP_INTERVAL_MS)

        # --- IPC Polling Timer ---
        if self.command_queue:
            self.ipc_timer = QTimer(self)
            self.ipc_timer.timeout.connect(self.check_queue)
            self.ipc_timer.start(100)  # Check every 100ms

    def check_queue(self):
        """Polls the multiprocessing queue for commands."""
        try:
            while not self.command_queue.empty():
                cmd = self.command_queue.get_nowait()
                self.handle_command(cmd)
        except queue.Empty:
            pass

    def handle_command(self, cmd):
        """Dispatches commands to modify Mom or trigger events."""
        msg_type = cmd.get("type")

        if msg_type == "throw_slipper":
            # Instantiate overlay directly within this process
            self.overlay = SlipperOverlay(self)
            self.overlay.show()

        elif msg_type == "set_expression":
            asset = cmd.get("asset", "mom.png")
            self.set_look(asset)

        elif msg_type == "show_blacklist_message":
            process_name = cmd.get("process", "unknown")
            self.show_blacklist_message(process_name)

    def show_blacklist_message(self, process_name):
        """Show a bubble with a message about the blacklisted process."""
        message = f"EH WHY ARE YOU RUNNING {process_name.upper()}??? STOP IT RIGHT NOW!"
        if not self.bubble:
            self.bubble = BubbleWidget(self.geometry(), [message])
        else:
            self.bubble.messages = [message]
            self.bubble.phrase_index = 0
            self.bubble.text = message
        self.bubble.set_target_geometry(self.geometry())
        self.bubble.show()
        self.bubble.activateWindow()
        # Restore original messages after 5 seconds
        QTimer.singleShot(5000, self.restore_bubble_messages)

    def restore_bubble_messages(self):
        """Restore the bubble to show original nagging messages."""
        if self.bubble:
            self.bubble.messages = self.original_messages
            self.bubble.phrase_index = 0
            self.bubble.text = self.original_messages[0] if self.original_messages else ""
            self.bubble.adjust_size_and_position()
            self.bubble.update()

    def load_pixmap(self, filename):
        img_path = get_asset_path(filename)
        pix = QPixmap(img_path)

        if pix.isNull():
            pix = QPixmap(100, 100)
            pix.fill(Qt.GlobalColor.red)
        else:
            if MOM_SCALE != 1.0:
                w = int(pix.width() * MOM_SCALE)
                h = int(pix.height() * MOM_SCALE)
                pix = pix.scaled(
                    w,
                    h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

        self.pixmap = pix
        self.resize(self.pixmap.size())
        self.update()

    def set_look(self, filename):
        self.load_pixmap(filename)

    def init_tray_icon(self, script_dir):
        icon_path = get_asset_path(ICON_FILENAME)
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
            )

        tray_menu = QMenu()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.show_bubble()

    def moveEvent(self, event):
        if self.bubble and self.bubble.isVisible():
            self.bubble.set_target_geometry(self.geometry())
        super().moveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def show_bubble(self):
        if not self.bubble:
            self.bubble = BubbleWidget(self.geometry(), self.messages)
        self.bubble.advance_phrase()
        self.bubble.set_target_geometry(self.geometry())
        self.bubble.show()
        self.bubble.activateWindow()

    def spawn_popup(self):
        self.popups = [p for p in self.popups if p.isVisible()]
        popup = PopupWidget()
        screen = self.screen().geometry()
        max_x = max(0, screen.width() - popup.width())
        max_y = max(0, screen.height() - popup.height())

        # Simple random position for brevity
        popup.move(random.randint(0, max_x), random.randint(0, max_y))
        popup.show()
        self.popups.append(popup)

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

def main(command_queue=None, messages=None):
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Pass queue to widget
    window = MomWidget(command_queue, messages)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
