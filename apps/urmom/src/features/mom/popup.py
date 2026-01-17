from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics

# Constants matched from original popup_window.py
POPUP_TEXT = "🥛"
POPUP_FONT = "Consolas"
POPUP_FONT_HEIGHT = 48  # Approx point size
POPUP_PAD_X = 12
POPUP_PAD_Y = 10

class PopupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Font setup
        self.font_obj = QFont(POPUP_FONT)
        self.font_obj.setPixelSize(POPUP_FONT_HEIGHT)
        self.font_obj.setBold(True)
        
        self.adjust_size()

    def adjust_size(self):
        fm = QFontMetrics(self.font_obj)
        text_w = fm.horizontalAdvance(POPUP_TEXT)
        text_h = fm.height()
        
        self.w = text_w + (POPUP_PAD_X * 2)
        self.h = text_h + (POPUP_PAD_Y * 2)
        self.resize(self.w, self.h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # No background, just text
        painter.setFont(self.font_obj)
        painter.setPen(QColor(0, 0, 0))
        
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            POPUP_TEXT
        )

    def mousePressEvent(self, event):
        self.close()