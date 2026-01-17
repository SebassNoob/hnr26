import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, 
    QLineEdit, QWidget, QStackedWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from features.bargain import negotiate_time

class BargainWorker(QThread):
    finished = pyqtSignal(dict)
    def __init__(self, excuse):
        super().__init__()
        self.excuse = excuse
    def run(self):
        result = negotiate_time(self.excuse)
        self.finished.emit(result)

class LightsOutDialog(QDialog):
    def __init__(self, minutes_left, mom_queue=None):
        super().__init__()
        self.minutes_left = minutes_left
        self.added_minutes = 0
        self.mom_queue = mom_queue

        self.setWindowTitle("UrMom - Lights Out!")
        self.resize(400, 300)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 14px; color: #333; }
            QPushButton { 
                background-color: #f0f0f0; border: 1px solid #ccc; 
                border-radius: 4px; padding: 8px; min-width: 80px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QLineEdit { padding: 5px; border: 1px solid #ccc; border-radius: 3px; }
        """)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)

        self._init_warn_screen()
        self._init_bargain_screen()
        self._init_loading_screen()
        self._init_result_screen()
        self.stack.setCurrentIndex(0)

    def _init_warn_screen(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)
        
        lbl = QLabel(f"⚠️ Lights out in {self.minutes_left} minutes!\n\nStart winding down.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(); font.setBold(True); font.setPointSize(16)
        lbl.setFont(font)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Okay Mom")
        btn_ok.clicked.connect(self.accept)
        btn_bargain = QPushButton("But wait...")
        btn_bargain.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_bargain)
        btn_layout.addStretch()

        layout.addStretch()
        layout.addWidget(lbl)
        layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()
        self.stack.addWidget(page)

    def _init_bargain_screen(self):
        page = QWidget()
        layout = QVBoxLayout()
        lbl = QLabel("Give me one good reason:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_excuse = QLineEdit()
        self.input_excuse.setPlaceholderText("I need to finish my assignment...")
        self.input_excuse.returnPressed.connect(self._submit_bargain)
        btn_submit = QPushButton("Ask Mom")
        btn_submit.clicked.connect(self._submit_bargain)
        layout.addStretch()
        layout.addWidget(lbl)
        layout.addWidget(self.input_excuse)
        layout.addWidget(btn_submit, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def _init_loading_screen(self):
        page = QWidget()
        layout = QVBoxLayout()
        lbl = QLabel("Mom is thinking...")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(); layout.addWidget(lbl); layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def _init_result_screen(self):
        self.page_result = QWidget()
        self.layout_result = QVBoxLayout()
        self.page_result.setLayout(self.layout_result)
        self.lbl_reply = QLabel("")
        self.lbl_reply.setWordWrap(True)
        self.lbl_reply.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_reply.setStyleSheet("font-style: italic; font-size: 16px;")
        self.lbl_added = QLabel("")
        self.lbl_added.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_added.setStyleSheet("font-weight: bold;")
        btn_close = QPushButton("Understood")
        btn_close.clicked.connect(self.accept)
        self.layout_result.addStretch()
        self.layout_result.addWidget(self.lbl_reply)
        self.layout_result.addWidget(self.lbl_added)
        self.layout_result.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout_result.addStretch()
        self.stack.addWidget(self.page_result)

    def _submit_bargain(self):
        excuse = self.input_excuse.text().strip()
        if not excuse: return
        self.stack.setCurrentIndex(2)
        self.worker = BargainWorker(excuse)
        self.worker.finished.connect(self._handle_bargain_result)
        self.worker.start()

    def _handle_bargain_result(self, result):
        self.added_minutes = result.get("minutes", 0)
        reply = result.get("reply", "...")
        
        # 1. Trigger Physical Punishment (if applicable)
        if result.get("slipper", False):
            if self.mom_queue:
                self.mom_queue.put({ "type": "throw_slipper" })
            
            # Note: We do NOT close the dialog here anymore.
            # We let it fall through to update the UI below so the user sees WHY.
        
        # 2. Update UI
        self.lbl_reply.setText(f'Mom says:\n"{reply}"')

        if self.added_minutes > 0:
            self.lbl_added.setText(f"✅ PASSED: +{self.added_minutes} minutes added.")
            self.lbl_added.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        else:
            # If slipper was thrown, make the text redder/angrier
            if result.get("slipper", False):
                 self.lbl_added.setText(f"💢 SLIPPER ATTACK! (+0 minutes)")
            else:
                 self.lbl_added.setText(f"❌ DENIED: +0 minutes.")
            
            self.lbl_added.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")

        self.stack.setCurrentIndex(3)

def show_warning_dialog(minutes_left, mom_queue=None):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    dialog = LightsOutDialog(minutes_left, mom_queue)
    dialog.show()
    dialog.raise_()
    dialog.activateWindow()
    app.exec()
    return dialog.added_minutes