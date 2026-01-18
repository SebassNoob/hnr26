import sys
import os
import random
import queue  # For the Empty exception
from utils import log
from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QUrl
from PyQt6.QtGui import QPixmap, QPainter, QAction, QIcon, QMouseEvent, QTransform
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from .bubble import BubbleWidget
from .popup import PopupWidget
import signal

from utils import log

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
        self.messages = list(messages) if messages else ["Drink some water.", "Sit up straight."]
        self.original_messages = list(self.messages)
        self.anger = 1  # Anger meter, 1 = normal, higher = angrier
        self.is_animating = False # Flag to prevent animations from overlapping

        # --- Audio Setup for Camera ---
        self.audio_output_camera = QAudioOutput()
        self.player_camera = QMediaPlayer()
        self.player_camera.setAudioOutput(self.audio_output_camera)
        self.player_camera.setSource(QUrl.fromLocalFile(get_asset_path("camera.mp3")))
        self.audio_output_camera.setVolume(1.0)
        # ------------------------------

        self.dragging = False
        self.drag_start_position = QPoint()
        self.bubble = None
        self.popups = []

        # 1. Chair Reminder (Sit up straight)
        QTimer.singleShot(30 * 1000, self.start_chair_reminders) # 0.5 min delay

        # 2. Water Reminder
        QTimer.singleShot(60 * 1000, self.start_water_reminders) # 1 min delay

        # 3. Grass Reminder (Take a break)
        QTimer.singleShot(120 * 1000, self.start_grass_reminders) # 2 min delay

        # Window Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Initial Load
        # Store the current "mood" image filename to revert to after animations
        self.current_look_filename = self.get_anger_image() 
        self.load_pixmap(self.current_look_filename)
        
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

        # Popup Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.spawn_popup)
        self.timer.start(POPUP_INTERVAL_MS)

        # --- IPC Polling Timer ---
        if self.command_queue:
            self.ipc_timer = QTimer(self)
            self.ipc_timer.timeout.connect(self.check_queue)
            self.ipc_timer.start(100) # Check every 100ms

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

        elif msg_type == "show_bubble_message":
            text = cmd.get("text", "...")
            score = cmd.get("score", 0.0)
            self.show_bubble(text=text, score=score)
            
        elif msg_type == "set_expression":
            asset = cmd.get("asset", "mom.png")
            self.set_look(asset)

        elif msg_type == "show_blacklist_message":
            process_name = cmd.get("process", "unknown")
            self.show_blacklist_message(process_name)

        elif msg_type == "change_anger":
            delta = cmd.get("delta", 0)
            self.update_anger(delta)
        
        elif msg_type == "prepare_for_screenshot":
            self.play_camera_animation()

    def get_anger_image(self):
        """Returns the image filename corresponding to the anger level."""
        if self.anger == 0:
            return "mom_smiling.png"
        elif self.anger == 1:
            return "mom.png"
        elif self.anger == 2:
            return "mom_sad.png"
        elif self.anger >= 3:
            return "mom_angry.png"
        else:
            log("Invalid anger level, defaulting to neutral")
            return "mom.png"

    def update_anger(self, delta):
        """Update the anger meter. If it reaches 4, trigger slipper and reset to 3."""
        self.anger += delta
        # --- CHANGE ---
        # Clamp anger at 0, but allow it to increase past 3.
        self.anger = max(0, min(4, self.anger))
        log(f"Anger updated to: {self.anger}")

        # Check for the slipper threshold
        if self.anger >= 4:
            log("Anger threshold reached! Throwing slipper.")
            
            # Trigger the slipper attack
            self.overlay = SlipperOverlay(self)
            self.overlay.show()
            
            # Reset anger back down to the "angry" state
            self.anger = 3

        # Update Mom's appearance based on the new anger level
        asset = self.get_anger_image()
        self.set_look(asset)

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

    def load_pixmap(self, filename, flip_horizontal=False):
        img_path = get_asset_path(filename)
        pix = QPixmap(img_path)
        
        if pix.isNull():
            pix = QPixmap(100, 100)
            pix.fill(Qt.GlobalColor.red)
        else:
            w = int(pix.width() * MOM_SCALE); h = int(pix.height() * MOM_SCALE)
            pix = pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        if flip_horizontal:
            transform = QTransform().scale(-1, 1)
            pix = pix.transformed(transform)
        
        self.pixmap = pix
        self.resize(self.pixmap.size())
        self.update()

    def set_look(self, filename, flip_horizontal=False):
        self.load_pixmap(filename, flip_horizontal)

    def play_camera_animation(self):
        """Plays the camera animation, flipping based on screen position."""
        if self.is_animating: return # Prevent overlapping animations
        self.is_animating = True

        screen_center_x = self.screen().geometry().width() / 2
        is_on_left_side = self.x() < screen_center_x

        # State 1: Pull out the camera
        self.set_look("mom_camera.png", flip_horizontal=is_on_left_side)

        def flash_and_snap():
            # State 2: Flash the camera and play sound
            self.set_look("mom_camera_flash.png", flip_horizontal=is_on_left_side)
            self.player_camera.setPosition(0) # Rewind sound
            self.player_camera.play()
            # Schedule the final state
            QTimer.singleShot(200, revert_to_normal)

        def revert_to_normal():
            # State 3: Revert to her normal mood appearance
            self.set_look(self.current_look_filename)
            self.is_animating = False # Release the animation lock

        # Schedule the flash
        QTimer.singleShot(750, flash_and_snap)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

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

    def show_bubble(self, text=None, score=None):
        if not self.bubble:
            self.bubble = BubbleWidget(self.geometry(), self.messages)
        
        # If text and score are provided, it's a WYD message
        if text is not None and score is not None:
            self.bubble.show_message(text, score)
        # Otherwise, it's a normal click, show the default phrase
        else:
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
    
    def cleanup_popups(self):
        """Removes references to closed popups to save memory."""
        self.popups = [p for p in self.popups if p.isVisible()]

    def start_chair_reminders(self):
        """Spawns the first chair popup and starts the recurring timer."""
        self.spawn_chair_popup()
        self.chair_timer = QTimer(self)
        self.chair_timer.timeout.connect(self.spawn_chair_popup)
        self.chair_timer.start(30 * 60 * 1000) # Every 30 mins

    def start_water_reminders(self):
        """Spawns the first water popup and starts the recurring timer."""
        self.spawn_water_popup()
        self.water_timer = QTimer(self)
        self.water_timer.timeout.connect(self.spawn_water_popup)
        self.water_timer.start(60 * 60 * 1000) # Every 1 hour

    def start_grass_reminders(self):
        """Spawns the first grass popup and starts the recurring timer."""
        self.spawn_grass_popup()
        self.grass_timer = QTimer(self)
        self.grass_timer.timeout.connect(self.spawn_grass_popup)
        self.grass_timer.start(30 * 60 * 1000) # Every 30 mins

    def spawn_chair_popup(self):
        self.cleanup_popups()
        popup = PopupWidget("chair.png", "Did you fix your posture?", "I've sat up straight")
        popup.show_randomly()
        self.popups.append(popup)

    def spawn_water_popup(self):
        self.cleanup_popups()
        popup = PopupWidget("water.png", "Time for some water!", "I've drank water")
        popup.show_randomly()
        self.popups.append(popup)

    def spawn_grass_popup(self):
        self.cleanup_popups()
        popup = PopupWidget("grass.png", "Go touch some grass.", "I've taken a break")
        popup.show_randomly()
        self.popups.append(popup)

    def quit_app(self):
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
