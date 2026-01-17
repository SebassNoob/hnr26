import sys
import os
import random
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QAction, QIcon, QMouseEvent

from .bubble import BubbleWidget
from .popup import PopupWidget

from utils.paths import get_asset_path

# Constants
IMAGE_FILENAME = "mom.png"
ICON_FILENAME = "mom.ico"
MOM_SCALE = 1.4
POPUP_INTERVAL_MS = 5000 * 60 * 3
SCREEN_EDGE_MARGIN = 16

class MomWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Load Resources
        script_dir = os.path.dirname(__file__)
        img_path = get_asset_path(IMAGE_FILENAME)
        self.pixmap = QPixmap(img_path)
        if self.pixmap.isNull():
            # Fallback red box
            self.pixmap = QPixmap(100, 100)
            self.pixmap.fill(Qt.GlobalColor.red)
        else:
            if MOM_SCALE != 1.0:
                w = int(self.pixmap.width() * MOM_SCALE)
                h = int(self.pixmap.height() * MOM_SCALE)
                self.pixmap = self.pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.resize(self.pixmap.size())
        
        # Initial Position (Bottom Right)
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
        self.init_tray_icon(script_dir)

        # Popup Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.spawn_popup)
        self.timer.start(POPUP_INTERVAL_MS)

    def init_tray_icon(self, script_dir):
        icon_path = get_asset_path(ICON_FILENAME)
        
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Fallback icon
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
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
            # If it was a short click (not a drag), show bubble
            # (Simple heuristic: if we didn't move much, it's a click)
            # Alternatively, just show bubble on release always if dragging finished
            self.show_bubble()

    def moveEvent(self, event):
        # Update bubble position if it exists
        if self.bubble and self.bubble.isVisible():
            self.bubble.set_target_geometry(self.geometry())
        super().moveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def show_bubble(self):
        if not self.bubble:
            self.bubble = BubbleWidget(self.geometry())
        
        # Cycle phrase
        self.bubble.advance_phrase()
        self.bubble.set_target_geometry(self.geometry())
        self.bubble.show()
        self.bubble.activateWindow()

    def spawn_popup(self):
        # Clean up closed popups
        self.popups = [p for p in self.popups if p.isVisible()]
        
        popup = PopupWidget()
        
        # Calculate Random Position avoiding Mom
        screen = self.screen().geometry()
        max_x = max(0, screen.width() - popup.width())
        max_y = max(0, screen.height() - popup.height())
        
        mom_rect = self.geometry()
        
        final_x, final_y = 0, 0
        found = False
        
        # Try 20 times to find a spot not overlapping Mom
        for _ in range(20):
            x = random.randint(0, max_x)
            y = random.randint(0, max_y)
            rect = QRect(x, y, popup.width(), popup.height())
            if not rect.intersects(mom_rect):
                final_x, final_y = x, y
                found = True
                break
        
        if not found:
            # Fallback corners
            candidates = [
                (0, 0),
                (max_x, 0),
                (0, max_y),
                (max_x, max_y)
            ]
            final_x, final_y = candidates[random.randint(0, 3)]

        popup.move(final_x, final_y)
        popup.show()
        self.popups.append(popup)

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

def main():
    # Allow Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep running for tray/popups even if bubble closes
    
    # Ensure resources are found if running from mom_2 folder directly
    # or if imported from root
    
    window = MomWidget()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()