"""
Wallpaper Window
A transparent, borderless, click-through PySide6 window pinned directly
to the desktop wallpaper layer above the user's static background.
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Optional
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QScreen

from core.system_agent import SystemAgent
from core.config_manager import ConfigManager
from ui.hud_painter import HUDPainter
from ui.themes import get_theme, THEMES

# Win32 Constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

HWND_BOTTOM = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

user32 = ctypes.windll.user32

class WallpaperWindow(QWidget):
    def __init__(self, agent: SystemAgent, config_mgr: ConfigManager):
        super().__init__()
        self.agent = agent
        self.config_mgr = config_mgr
        self.painter_engine = HUDPainter(self.config_mgr)
        
        self.tick = 0
        self.current_theme = get_theme(self.config_mgr.get("theme", "cyber_neon"))
        
        # Multi-HUD View & Transition State
        self.view_mode = 0             # 0: Live Telemetry HUD, 1: Game Performance Report HUD
        self.transition_progress = 0.0 # 0.0 = Telemetry, 1.0 = Game Report
        self.transition_target = 0.0
        self._cached_snapshot = None
        
        # Debrief Auto-Dismiss Timer State
        self.report_countdown_sec = 0.0
        self.report_timer_paused = False
        
        # Configure Qt window attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._apply_qt_flags()
        
        # Match primary screen geometry
        self._setup_geometry()
        
        # Configure Win32 styles (click-through & bottom Z-order)
        self.setup_win32_styles()
        
        # Animation timer (default 30 FPS = ~33ms)
        fps = max(10, min(60, int(self.config_mgr.get("fps", 30))))
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_animation_frame)
        self.anim_timer.start(int(1000 / fps))
        
        # Periodic Z-Order enforcement timer (ensures wallpaper pinning persists across Win+D)
        self.zorder_timer = QTimer(self)
        self.zorder_timer.timeout.connect(self._enforce_zorder)
        self.zorder_timer.start(1500)

    def _setup_geometry(self):
        screen = QApplication.primaryScreen()
        pos = self.config_mgr.get("screen_position", "right_half")
        if screen:
            geo = screen.geometry()
            sx = geo.x()
            sy = geo.y()
            sw = geo.width()
            sh = geo.height()
            
            if pos == "right_half":
                half_w = sw // 2
                self.setGeometry(sx + half_w, sy, sw - half_w, sh)
            elif pos == "left_half":
                half_w = sw // 2
                self.setGeometry(sx, sy, half_w, sh)
            else:  # "fullscreen"
                self.setGeometry(sx, sy, sw, sh)
        else:
            if pos == "right_half":
                self.setGeometry(960, 0, 960, 1080)
            elif pos == "left_half":
                self.setGeometry(0, 0, 960, 1080)
            else:
                self.setGeometry(0, 0, 1920, 1080)

    def _apply_qt_flags(self):
        mode = self.config_mgr.get("mode", "wallpaper")
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if mode == "wallpaper":
            flags |= Qt.WindowType.WindowStaysOnBottomHint
        else:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def setup_win32_styles(self):
        """Applies Windows extended styles for click-through and desktop pinning."""
        hwnd = int(self.winId())
        if not hwnd:
            return

        click_through = self.config_mgr.get("click_through", True)
        mode = self.config_mgr.get("mode", "wallpaper")

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= (WS_EX_LAYERED | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        
        if click_through:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT

        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self._enforce_zorder()

    def _enforce_zorder(self):
        """Enforces desktop wallpaper layer positioning."""
        hwnd = int(self.winId())
        if not hwnd:
            return

        mode = self.config_mgr.get("mode", "wallpaper")
        if mode == "wallpaper":
            user32.SetWindowPos(
                hwnd,
                HWND_BOTTOM,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )
        else:
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )

    def _on_animation_frame(self):
        self.tick += 1
        
        # Thread-safe check for new game report directly on main GUI thread
        self._cached_snapshot = self.agent.get_snapshot()
        if self._cached_snapshot and self._cached_snapshot.get("has_new_game_report"):
            self.agent.clear_new_game_report_flag()
            self.switch_to_view(1, auto_countdown=True)
        
        # Step view transition animation smoothly
        if abs(self.transition_progress - self.transition_target) > 0.001:
            step = 0.075 # ~13 frames = ~400ms smooth transition
            if self.transition_progress < self.transition_target:
                self.transition_progress = min(self.transition_target, self.transition_progress + step)
            else:
                self.transition_progress = max(self.transition_target, self.transition_progress - step)
            if self.transition_progress == self.transition_target:
                self.view_mode = int(self.transition_target)
                
        # Game Report Auto-Dismiss Timer Logic
        if self.view_mode == 1 and not self.report_timer_paused and self.report_countdown_sec > 0:
            fps = max(10, min(60, int(self.config_mgr.get("fps", 30))))
            dt = 1.0 / fps
            self.report_countdown_sec = max(0.0, self.report_countdown_sec - dt)
            if self.report_countdown_sec <= 0.0:
                self.report_countdown_sec = 0.0
                self.switch_to_view(0)

        self.update()

    def switch_to_view(self, target_view: int, auto_countdown: bool = True):
        """Triggers smooth animated transition to target view (0: Live Telemetry, 1: Game Report)."""
        self.transition_target = float(target_view)
        if target_view == 1:
            dismiss_sec = float(self.config_mgr.get("game_report_auto_dismiss_sec", 150))
            if dismiss_sec > 0 and auto_countdown:
                self.report_countdown_sec = dismiss_sec
                self.report_timer_paused = False
        else:
            self.report_countdown_sec = 0.0
            self.report_timer_paused = False
        self.update()

    def toggle_report_timer_pause(self):
        """Pauses or resumes the debrief auto-dismiss countdown timer."""
        self.report_timer_paused = not self.report_timer_paused
        self.update()

    def set_report_timer_duration(self, sec: float):
        """Configures the debrief auto-dismiss duration and persists it."""
        self.config_mgr.set("game_report_auto_dismiss_sec", sec)
        if self.view_mode == 1 and sec > 0:
            self.report_countdown_sec = float(sec)
            self.report_timer_paused = False
        elif sec <= 0:
            self.report_countdown_sec = 0.0
        self.update()

    def toggle_view(self):
        """Toggles between Telemetry HUD and Game Report HUD with smooth animation."""
        new_target = 1 if self.transition_target < 0.5 else 0
        self.switch_to_view(new_target)

    def keyPressEvent(self, event):
        """Allows hotkey toggling (T key)."""
        if event.key() == Qt.Key.Key_T:
            self.toggle_view()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        snapshot = self._cached_snapshot or self.agent.get_snapshot()
        self.painter_engine.paint(
            painter,
            self.width(),
            self.height(),
            snapshot,
            self.tick,
            self.current_theme,
            view_mode=self.view_mode,
            transition_progress=self.transition_progress,
            report_countdown_sec=self.report_countdown_sec,
            report_timer_paused=self.report_timer_paused
        )

    # Runtime configuration hooks
    def set_theme(self, theme_key: str):
        self.current_theme = get_theme(theme_key)
        self.config_mgr.set("theme", theme_key)
        self.update()

    def set_display_mode(self, mode: str):
        self.config_mgr.set("mode", mode)
        self._apply_qt_flags()
        self.show()
        self.setup_win32_styles()
        self.update()

    def set_click_through(self, enabled: bool):
        self.config_mgr.set("click_through", enabled)
        self.setup_win32_styles()

    def set_layout(self, layout_name: str):
        self.config_mgr.set("layout", layout_name)
        self.update()

    def set_opacity(self, opacity: float):
        self.config_mgr.set("opacity", opacity)
        self.update()

    def set_screen_position(self, pos: str):
        self.config_mgr.set("screen_position", pos)
        self._setup_geometry()
        self.setup_win32_styles()
        self.update()

    def set_panel_backdrop(self, enabled: bool):
        self.config_mgr.set("panel_backdrop", enabled)
        self.update()

    def set_fps(self, fps: int):
        self.config_mgr.set("fps", fps)
        self.anim_timer.setInterval(int(1000 / fps))
