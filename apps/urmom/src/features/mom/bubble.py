import sys
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QPen, QFontMetrics

# Constants matched from original bubble_window.py
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

        self.messages = messages if messages else ["Have you eaten yet?"]
        self.phrase_index = 0
        self.text = self.messages[0] if self.messages else "Don't poke me."
        self.is_wyd_message = False
        self.score = 0.0
        
        self.tail_center_x = None  # If set, overrides standard offset
        self.target_geometry = parent_geometry # The rect of the Mom window
        self.target_point = None  # Screen-space point to aim the tail at
        
        # Font setup
        self.font_obj = QFont(BUBBLE_FONT)
        self.font_obj.setPixelSize(BUBBLE_FONT_HEIGHT)
        self.font_obj.setBold(True)

    def advance_phrase(self):
        # Cycle through nagging messages when clicking mom
        self.is_wyd_message = False
        if self.messages:
            self.text = self.messages[self.phrase_index % len(self.messages)]
            self.phrase_index += 1
        else:
            self.text = "Don't poke me."
        self.adjust_size_and_position()
        self.update()

    def show_message(self, text, score):
        self.text = text
        self.score = score
        self.is_wyd_message = True
        self.adjust_size_and_position()
        self.update()

    def set_target_geometry(self, rect):
        self.target_geometry = rect
        self.target_point = None
        self.adjust_size_and_position()

    def set_target_point(self, point):
        self.target_point = point
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
        
        # Add extra height for the score text if it's a WYD message
        extra_h = 20 if self.is_wyd_message else 0
        self.bubble_h = text_h + (BUBBLE_PAD_Y * 2) + extra_h
        
        total_w = self.bubble_w + 2 # Padding for border stroke
        total_h = self.bubble_h + TAIL_HEIGHT + 2

        self.resize(total_w, total_h)
        
        # Position logic
        screen = self.screen().geometry()
        margin = 16

        if self.target_point:
            # Position above Mom's head
            head_x = self.target_point.x()
            head_y = self.target_point.y()
        elif self.target_geometry:
            # Fallback: position above Mom's center
            head_x = self.target_geometry.x() + (self.target_geometry.width() // 2)
            head_y = self.target_geometry.y() + 20
        else:
            head_x = None
            head_y = None

        if head_x is not None and head_y is not None:
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

        # Draw the productivity score if it's a WYD message
        if self.is_wyd_message:
            status_text = "Neutral"
            status_color = QColor(128, 128, 128) # Gray
            if self.score > 0.3:
                status_text = "Productive"
                status_color = QColor(0, 150, 0) # Green
            elif self.score < -0.3:
                status_text = "Unproductive"
                status_color = QColor(200, 0, 0) # Red

            painter.setPen(status_color)
            status_font = QFont(BUBBLE_FONT)
            status_font.setPixelSize(14)
            painter.setFont(status_font)
            
            # Position it at the bottom of the bubble
            painter.drawText(
                QRectF(text_rect.x(), self.bubble_h - 22, text_rect.width(), 20),
                Qt.AlignmentFlag.AlignRight,
                f"[{status_text}]"
            )

    def mousePressEvent(self, event):
        # Click to close
        self.close()
