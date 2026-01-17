import sys
import os
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QPainter, QPixmap, QTransform
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from utils.paths import get_asset_path

class SlipperOverlay(QWidget):
    def __init__(self, mom_instance):
        super().__init__()
        self.mom = mom_instance
        
        # Overlay Setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Match Screen Geometry
        screen = self.mom.screen()
        self.setGeometry(screen.geometry())
        
        self.center_x = self.width() // 2
        self.center_y = self.height() // 2
        
        mom_rect = self.mom.geometry()
        self.launch_x = mom_rect.x() + (mom_rect.width() // 2)
        self.launch_y = mom_rect.y() + (mom_rect.height() // 3)

        self.assets = {
            "slipper_1": QPixmap(get_asset_path("slipper_1.png")),
            "slipper_2": QPixmap(get_asset_path("slipper_2.png")),
            "slipper_3": QPixmap(get_asset_path("slipper_3.png")),
            "slipper_splat": QPixmap(get_asset_path("slipper_4.png")),
        }
        
        # --- Audio Setup ---
        self.audio_output_throw = QAudioOutput()
        self.player_throw = QMediaPlayer()
        self.player_throw.setAudioOutput(self.audio_output_throw)
        self.player_throw.setSource(QUrl.fromLocalFile(get_asset_path("throw.mp3")))
        self.audio_output_throw.setVolume(1.0)

        self.audio_output_slap = QAudioOutput()
        self.player_slap = QMediaPlayer()
        self.player_slap.setAudioOutput(self.audio_output_slap)
        self.player_slap.setSource(QUrl.fromLocalFile(get_asset_path("slap.mp3")))
        self.audio_output_slap.setVolume(1.0)
        # -------------------

        self.state = "WINDUP" 
        self.ticks = 0
        self.opacity = 1.0
        self.throw_progress = 0.0
        self.slipper_rotation = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) 
        
        self.mom.set_look("mom_slipper.png")

    def update_animation(self):
        self.ticks += 1

        if self.state == "WINDUP":
            if self.ticks > 30:
                self.state = "THROWING"
                self.mom.set_look("mom_slipper_thrown.png")
                # Play throw sound
                self.player_throw.play()
                self.ticks = 0

        elif self.state == "THROWING":
            self.throw_progress += 0.05 # Slightly faster
            self.slipper_rotation += 45
            
            if self.throw_progress >= 1.0:
                self.state = "SPLAT"
                self.ticks = 0
                # Play splat sound
                self.player_slap.play()

        elif self.state == "SPLAT":
            if self.ticks > 120:
                self.state = "FADE"
                self.ticks = 0
                self.mom.set_look("mom.png")
        
        elif self.state == "FADE":
            self.opacity -= 0.05
            if self.opacity <= 0:
                self.close()

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(self.opacity)

        if self.state == "THROWING":
            frame_idx = (self.ticks // 4) % 3
            pix = self.assets[f"slipper_{frame_idx + 1}"]
            
            cur_x = self.launch_x + (self.center_x - self.launch_x) * self.throw_progress
            cur_y = self.launch_y + (self.center_y - self.launch_y) * self.throw_progress
            
            scale = 0.5 + (2.5 * self.throw_progress)
            
            t = QTransform()
            t.translate(cur_x, cur_y)
            t.rotate(self.slipper_rotation)
            t.scale(scale, scale)
            t.translate(-pix.width()/2, -pix.height()/2)
            
            painter.setTransform(t)
            painter.drawPixmap(0, 0, pix)
            painter.resetTransform()

        elif self.state in ["SPLAT", "FADE"]:
            pix = self.assets["slipper_splat"]
            scale = 3.0
            
            t = QTransform()
            t.translate(self.center_x, self.center_y)
            t.scale(scale, scale)
            t.translate(-pix.width()/2, -pix.height()/2)
            
            painter.setTransform(t)
            painter.drawPixmap(0, 0, pix)
            painter.resetTransform()

    def closeEvent(self, event):
        if self.mom:
            self.mom.set_look("mom.png")
        super().closeEvent(event)