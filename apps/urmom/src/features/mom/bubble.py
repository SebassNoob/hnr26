import sys
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QPen, QFontMetrics

BUBBLE_FONT = "Consolas"
BUBBLE_FONT_HEIGHT = 18  # Approx conversion from height 24 logfont
BUBBLE_PAD_X = 14
BUBBLE_PAD_Y = 12
BUBBLE_MAX_WIDTH = 260
TAIL_WIDTH = 18
TAIL_HEIGHT = 12
TAIL_OFFSET_X = 28
BUBBLE_BG = QColor(255, 255, 255)
BUBBLE_BORDER = QColor(0, 0, 0)
TEXT_COLOR = QColor(0, 0, 0)

class BubbleWidget(QWidget):
    def __init__(self, parent_geometry=None, messages=None):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.messages = messages if messages else ["Drink some water.", "Sit up straight."]
        self.phrase_index = 0
        self.text = self.messages[0]
        self.tail_center_x = None  # If set, overrides standard offset
        self.target_geometry = parent_geometry # The rect of the Mom window
        
        # Font setup
        self.font_obj = QFont(BUBBLE_FONT)
        self.font_obj.setPixelSize(BUBBLE_FONT_HEIGHT)
        self.font_obj.setBold(True)

    def advance_phrase(self):
        self.phrase_index = (self.phrase_index + 1) % len(self.messages)
        self.text = self.messages[self.phrase_index]
        self.adjust_size_and_position()
        self.update()

    def set_target_geometry(self, rect):
        self.target_geometry = rect
        self.adjust_size_and_position()

    def adjust_size_and_position(self):
        # Measure text
        fm = QFontMetrics(self.font_obj)
        rect = fm.boundingRect(
            0, 0, 
            BUBBLE_MAX_WIDTH, 1000, 
            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft, 
            self.text
        )
        
        text_w = rect.width()
        text_h = rect.height()

        self.bubble_w = text_w + (BUBBLE_PAD_X * 2)
        self.bubble_h = text_h + (BUBBLE_PAD_Y * 2)
        
        total_w = self.bubble_w + 2 # Padding for border stroke
        total_h = self.bubble_h + TAIL_HEIGHT + 2

        self.resize(total_w, total_h)
        
        # Position logic
        screen = self.screen().geometry()
        margin = 16

        if self.target_geometry:
            # Position above Mom
            head_x = self.target_geometry.x() + (self.target_geometry.width() // 2)
            head_y = self.target_geometry.y() + 20 
            
            bx = head_x - (self.bubble_w // 2)
            by = head_y - self.bubble_h - 10
            
            # Clamp to screen
            bx = max(margin, min(bx, screen.width() - self.bubble_w - margin))
            by = max(margin, min(by, screen.height() - self.bubble_h - margin))
            
            # Calculate tail relative to bubble
            self.tail_center_x = head_x - bx
        else:
            # Random logic handled externally or default center
            bx = (screen.width() - self.bubble_w) // 2
            by = (screen.height() - self.bubble_h) // 2
            self.tail_center_x = None

        self.move(int(bx), int(by))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Setup Pen/Brush
        pen = QPen(BUBBLE_BORDER)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(BUBBLE_BG)

        # Draw Bubble Shape
        path = QPainterPath()
        
        # Main rounded rect
        rect_bottom = self.bubble_h
        path.addRoundedRect(1, 1, self.bubble_w, rect_bottom, 12, 12)
        
        # Tail
        if self.tail_center_x is not None:
            # Clamp tail to be within bubble
            t_center = max(TAIL_WIDTH, min(self.bubble_w - TAIL_WIDTH, self.tail_center_x))
        else:
            t_center = TAIL_OFFSET_X + (TAIL_WIDTH // 2)
            
        t_left = t_center - (TAIL_WIDTH // 2)
        t_right = t_center + (TAIL_WIDTH // 2)
        
        tail_path = QPainterPath()
        tail_path.moveTo(t_left, rect_bottom)
        tail_path.lineTo(t_right, rect_bottom)
        tail_path.lineTo(t_center, rect_bottom + TAIL_HEIGHT)
        tail_path.closeSubpath()
        
        # Combine paths
        final_path = path.united(tail_path)
        painter.drawPath(final_path)

        # Draw Text
        painter.setPen(TEXT_COLOR)
        painter.setFont(self.font_obj)
        
        text_rect = QRectF(
            BUBBLE_PAD_X + 1, 
            BUBBLE_PAD_Y + 1, 
            self.bubble_w - (BUBBLE_PAD_X * 2), 
            self.bubble_h - (BUBBLE_PAD_Y * 2)
        )
        painter.drawText(
            text_rect, 
            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignLeft, 
            self.text
        )

    def mousePressEvent(self, event):
        # Click to close
        self.close()