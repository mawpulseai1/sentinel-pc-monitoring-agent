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
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
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

WM_NCHITTEST = 0x0084
HTTRANSPARENT = -1
HTCLIENT = 1

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
        self.view_mode = 0             # 0: Live Telemetry HUD, 1: Game Debrief HUD, 2: News Sentry HUD
        self.from_view = 0
        self.to_view = 0
        self.transition_target = 0.0   # Compatibility property
        self.transition_progress = 1.0 # 1.0 = fully switched
        self._cached_snapshot = None
        
        # Debrief Auto-Dismiss Timer State
        self.report_countdown_sec = 0.0
        self.report_timer_paused = False

        # HUD Auto-Rotation State (Rotates between Telemetry & News HUD)
        self.auto_rotate_enabled = bool(self.config_mgr.get("auto_rotate_hud", True))
        self.auto_rotate_interval = float(self.config_mgr.get("hud_rotation_interval_sec", 45))
        self.auto_rotate_countdown = self.auto_rotate_interval
        
        # Interactive Hit-Testing & Hover States
        self.setMouseTracking(True)
        self.hovered_item_id = None
        self.toast_message = ""
        self.toast_timer = 0.0
        
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

        click_through = self.config_mgr.get("click_through", False)
        mode = self.config_mgr.get("mode", "wallpaper")

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= (WS_EX_LAYERED | WS_EX_TOOLWINDOW)
        
        # When viewing News (view 2) or when click_through is disabled:
        # Guarantee 100% clickability, selection, and mouse event delivery!
        if click_through and self.view_mode != 2:
            style |= (WS_EX_TRANSPARENT | WS_EX_NOACTIVATE)
        else:
            style &= ~WS_EX_TRANSPARENT
            style &= ~WS_EX_NOACTIVATE

        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self._enforce_zorder()

    def _enforce_zorder(self):
        """Enforces desktop wallpaper layer positioning."""
        hwnd = int(self.winId())
        if not hwnd:
            return

        mode = self.config_mgr.get("mode", "wallpaper")
        # In News HUD (view 2) or overlay mode: bring to the top so it's directly visible and clickable
        if self.view_mode == 2 or mode == "overlay":
            user32.SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            )
        else:
            user32.SetWindowPos(
                hwnd,
                HWND_BOTTOM,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
            )

    def _on_animation_frame(self):
        self.tick += 1
        fps = max(10, min(60, int(self.config_mgr.get("fps", 30))))
        dt = 1.0 / fps
        
        # Thread-safe check for new game report directly on main GUI thread
        self._cached_snapshot = self.agent.get_snapshot()
        if self._cached_snapshot and self._cached_snapshot.get("has_new_game_report"):
            self.agent.clear_new_game_report_flag()
            self.switch_to_view(1, auto_countdown=True)
        
        # Step multi-view sliding transition animation smoothly
        if self.transition_progress < 1.0:
            step = 0.08 # ~12 frames = ~380ms smooth slide
            self.transition_progress = min(1.0, self.transition_progress + step)
            if self.transition_progress >= 1.0:
                self.view_mode = self.to_view
                self.from_view = self.to_view
                
        # Game Report Auto-Dismiss Timer Logic
        if self.view_mode == 1 and not self.report_timer_paused and self.report_countdown_sec > 0:
            self.report_countdown_sec = max(0.0, self.report_countdown_sec - dt)
            if self.report_countdown_sec <= 0.0:
                self.report_countdown_sec = 0.0
                self.switch_to_view(0)

        # HUD Auto-Rotation Logic (Rotates between Telemetry [0] and News [2])
        if self.auto_rotate_enabled and self.view_mode != 1 and self.transition_progress >= 1.0:
            self.auto_rotate_countdown = max(0.0, self.auto_rotate_countdown - dt)
            if self.auto_rotate_countdown <= 0.0:
                self.auto_rotate_countdown = self.auto_rotate_interval
                next_v = 2 if self.view_mode == 0 else 0
                self.switch_to_view(next_v)

        # Toast message timer
        if self.toast_timer > 0.0:
            self.toast_timer = max(0.0, self.toast_timer - dt)
            if self.toast_timer <= 0.0:
                self.toast_message = ""

        self.update()

    def switch_to_view(self, target_view: int, auto_countdown: bool = True):
        """Triggers smooth animated slide transition to target view (0: Telemetry, 1: Game Report, 2: News Sentry)."""
        target_int = int(target_view)
        self.transition_target = float(target_int)
        if target_int == self.to_view and self.transition_progress >= 0.999:
            return

        self.from_view = self.view_mode
        self.to_view = target_int
        self.transition_progress = 0.0
        
        if target_int == 1:
            dismiss_sec = float(self.config_mgr.get("game_report_auto_dismiss_sec", 150))
            if dismiss_sec > 0 and auto_countdown:
                self.report_countdown_sec = dismiss_sec
                self.report_timer_paused = False
        else:
            self.report_countdown_sec = 0.0
            self.report_timer_paused = False

        # Reset auto-rotate countdown on manual view switches
        self.auto_rotate_countdown = self.auto_rotate_interval
        self.setup_win32_styles()
        self.update()

    def toggle_auto_rotate(self) -> bool:
        """Toggles automatic periodic rotation between Telemetry HUD and News HUD."""
        self.auto_rotate_enabled = not self.auto_rotate_enabled
        self.config_mgr.set("auto_rotate_hud", self.auto_rotate_enabled)
        self.auto_rotate_countdown = self.auto_rotate_interval
        self.update()
        return self.auto_rotate_enabled

    def set_auto_rotate_interval(self, sec: float):
        """Sets the auto-rotation period in seconds (e.g. 30s, 45s, 60s)."""
        self.auto_rotate_interval = max(10.0, float(sec))
        self.config_mgr.set("hud_rotation_interval_sec", self.auto_rotate_interval)
        self.auto_rotate_countdown = self.auto_rotate_interval
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
        """Cycles between Telemetry HUD and News HUD with smooth slide animation."""
        new_target = 2 if self.to_view == 0 else 0
        self.switch_to_view(new_target)

    def nativeEvent(self, eventType, message):
        """Smart Win32 hit-testing: grants 100% clickability on News HUD and over interactive buttons."""
        if eventType in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg = wintypes.MSG.from_address(message.__int__())
                if msg.message == WM_NCHITTEST:
                    # In News HUD (view 2) or when click_through is disabled:
                    # The HUD is 100% clickable everywhere!
                    if self.view_mode == 2 or not self.config_mgr.get("click_through", False):
                        return (True, HTCLIENT)

                    # When click_through is enabled in other views, check if mouse is over interactive buttons/cards
                    x = wintypes.SHORT(msg.lParam & 0xFFFF).value
                    y = wintypes.SHORT((msg.lParam >> 16) & 0xFFFF).value
                    local_pt = self.mapFromGlobal(QPoint(x, y))

                    for rect, _ in getattr(self.painter_engine, "news_click_rects", []):
                        if rect.contains(local_pt):
                            return (True, HTCLIENT)
                    for rect, _ in getattr(self.painter_engine, "button_click_rects", []):
                        if rect.contains(local_pt):
                            return (True, HTCLIENT)

                    return (True, HTTRANSPARENT)
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def mouseMoveEvent(self, event):
        """Detects mouse hover over interactive news cards and buttons."""
        pos = event.position().toPoint()
        found_hover = None
        for rect, news_id in getattr(self.painter_engine, "news_click_rects", []):
            if rect.contains(pos):
                found_hover = news_id
                break
        if not found_hover:
            for rect, action_tag in getattr(self.painter_engine, "button_click_rects", []):
                if rect.contains(pos):
                    found_hover = action_tag
                    break

        if found_hover != self.hovered_item_id:
            self.hovered_item_id = found_hover
            if found_hover:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Handles interactive clicks on expandable news items, copy buttons, and HUD controls."""
        pos = event.position().toPoint()
        handled = False

        # 1. Check Button Clicks
        for rect, action_tag in getattr(self.painter_engine, "button_click_rects", []):
            if rect.contains(pos):
                handled = True
                if action_tag.startswith("copy_"):
                    item_id = action_tag.replace("copy_", "")
                    self._copy_news_item_to_clipboard(item_id)
                elif action_tag == "nav_tel":
                    self.switch_to_view(0)
                elif action_tag == "nav_news":
                    self.switch_to_view(2)
                elif action_tag == "nav_rot":
                    self.toggle_auto_rotate()
                elif action_tag == "nav_sweep":
                    self.agent.refresh_news_now()
                    self.toast_message = "⚡ RUNNING REAL-TIME INTELLIGENCE SWEEP..."
                    self.toast_timer = 3.0
                    self.update()
                break

        # 2. Check News Card Clicks (Expand / Collapse)
        if not handled:
            for rect, news_id in getattr(self.painter_engine, "news_click_rects", []):
                if rect.contains(pos):
                    self.agent.toggle_news_expansion(news_id)
                    handled = True
                    self.update()
                    break

        super().mousePressEvent(event)

    def _copy_news_item_to_clipboard(self, news_id: str):
        """Copies verified news briefing, proof, and live social user chatter to Windows clipboard."""
        snap = self._cached_snapshot or self.agent.get_snapshot()
        items = snap.get("news", {}).get("items", [])
        for item in items:
            if item.get("id") == news_id:
                clip_text = f"[{item.get('category')}] {item.get('title')}\n"
                clip_text += f"{item.get('summary')}\n"
                clip_text += f"Verification: {item.get('credibility_percent')}%, Proof: {item.get('fact_check_note')}\n\n"
                clip_text += "Live Public Chatter:\n"
                for p in item.get("live_posts", []):
                    clip_text += f"• {p.get('handle')} ({p.get('author')}): \"{p.get('content')}\" (👍 {p.get('likes')})\n"
                QApplication.clipboard().setText(clip_text)
                self.toast_message = "✓ COPIED VERIFIED INTEL TO CLIPBOARD!"
                self.toast_timer = 3.0
                self.update()
                break

    def keyPressEvent(self, event):
        """Hotkey controls: T (Telemetry), N (News), G (Game), R (Auto-Rotate), Space (Expand News)."""
        key = event.key()
        if key == Qt.Key.Key_T:
            self.switch_to_view(0)
        elif key == Qt.Key.Key_N:
            self.switch_to_view(2)
        elif key == Qt.Key.Key_G:
            self.switch_to_view(1)
        elif key == Qt.Key.Key_R:
            self.toggle_auto_rotate()
        elif key == Qt.Key.Key_Space:
            # Toggle expansion of currently visible news item
            snap = self._cached_snapshot or self.agent.get_snapshot()
            news_items = snap.get("news", {}).get("items", [])
            if news_items:
                cur_exp = snap.get("news", {}).get("expanded_news_id")
                next_id = news_items[0]["id"] if not cur_exp else cur_exp
                self.agent.toggle_news_expansion(next_id)
                self.update()
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
            from_view=self.from_view,
            to_view=self.to_view,
            transition_progress=self.transition_progress,
            report_countdown_sec=self.report_countdown_sec,
            report_timer_paused=self.report_timer_paused,
            auto_rotate_countdown_sec=self.auto_rotate_countdown if self.auto_rotate_enabled else -1.0,
            hovered_item_id=self.hovered_item_id,
            toast_message=self.toast_message
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
