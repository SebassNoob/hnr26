# src/features/mom/popup.py

import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

from utils.paths import get_asset_path

class PopupWidget(QWidget):
    def __init__(self, image_file, text, button_text):
        super().__init__()

        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # OUTER layout (transparent)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # CONTENT widget (rounded card)
        content = QWidget(self)
        content.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid black;
                border-radius: 10px;
            }
            QLabel {
                font-family: 'Consolas';
                font-size: 16px;
                font-weight: bold;
                color: black;
                border: none;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas';
                color: black;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        outer_layout.addWidget(content)

        # INNER layout (padding inside card)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. Image
        image_label = QLabel()
        pixmap = QPixmap(get_asset_path(image_file))
        pixmap = pixmap.scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        # 2. Text
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)

        # 3. Button
        button = QPushButton(button_text)
        button.clicked.connect(self.close)
        layout.addWidget(button)

        self.adjustSize()


    def show_randomly(self):
        """Positions and shows the widget at a random screen location."""
        screen_geo = self.screen().geometry()
        max_x = max(0, screen_geo.width() - self.width() - 20)
        max_y = max(0, screen_geo.height() - self.height() - 20)
        
        self.move(random.randint(0, max_x), random.randint(0, max_y))
        self.show()

    def mousePressEvent(self, event):
        # Allow dragging the popup
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
