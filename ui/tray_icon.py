"""
System Tray Controller
Provides a Windows taskbar tray icon with interactive controls for themes,
display modes, click-through, layouts, and system agent management.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PySide6.QtCore import Qt

from ui.themes import THEMES

def create_tray_pixmap(color_hex: str = "#00f0ff") -> QPixmap:
    """Generates a high-DPI cyberpunk cyber-core tray icon."""
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    
    # Outer cyber ring
    c = QColor(color_hex)
    painter.setPen(c)
    painter.setBrush(QColor(0, 0, 0, 160))
    painter.drawEllipse(2, 2, 28, 28)
    
    # Center glowing core
    c_core = QColor(c)
    c_core.setAlpha(220)
    painter.setBrush(c_core)
    painter.drawEllipse(10, 10, 12, 12)
    
    # Center pulse dot
    painter.setBrush(QColor(255, 255, 255))
    painter.drawEllipse(13, 13, 6, 6)
    
    painter.end()
    return pix

class SystemTrayController:
    def __init__(self, window, agent, config_mgr):
        self.window = window
        self.agent = agent
        self.config_mgr = config_mgr
        
        self.tray = QSystemTrayIcon()
        self.pixmap = create_tray_pixmap("#00f0ff")
        self.tray.setIcon(QIcon(self.pixmap))
        self.tray.setToolTip("PC Monitoring Agent // Animated Wallpaper HUD")
        
        self._build_menu()
        self.tray.show()

    def _build_menu(self):
        menu = QMenu()
        
        # Header / Status
        status_action = menu.addAction("◈ AGENT SENTINEL: ACTIVE")
        status_action.setEnabled(False)
        menu.addSeparator()

        # HUD View Navigation Submenu (Animated View Switcher)
        view_menu = menu.addMenu("Active HUD View")
        v_telemetry = view_menu.addAction("Live System Telemetry HUD")
        v_telemetry.setCheckable(True)
        v_telemetry.setChecked(self.window.transition_target < 0.5)
        v_telemetry.triggered.connect(lambda: self._switch_hud_view(0, v_telemetry, v_game))

        v_game = view_menu.addAction("Game Performance Report HUD")
        v_game.setCheckable(True)
        v_game.setChecked(self.window.transition_target >= 0.5)
        v_game.triggered.connect(lambda: self._switch_hud_view(1, v_telemetry, v_game))

        # Game Sentinel Controls
        game_menu = menu.addMenu("Game Sentinel Controls")
        g_start = game_menu.addAction("🎮 Start Tracking Active Window as Game")
        g_start.triggered.connect(self._start_manual_game)
        
        g_stop = game_menu.addAction("⏹ Stop Tracking & Show Debrief")
        g_stop.triggered.connect(self._stop_manual_game)

        g_sim = game_menu.addAction("⚡ Simulate Game Report (Test Animation)")
        g_sim.triggered.connect(self._trigger_simulated_game)

        # Debrief Auto-Dismiss Timer Submenu
        timer_menu = menu.addMenu("Debrief Auto-Return Timer")
        cur_timer = float(self.config_mgr.get("game_report_auto_dismiss_sec", 150))
        
        timer_opts = [
            (150, "2.5 Minutes (Default)"),
            (60, "1 Minute"),
            (300, "5 Minutes"),
            (0, "Disabled (Stay on Debrief)")
        ]
        for t_sec, t_lbl in timer_opts:
            tact = timer_menu.addAction(t_lbl)
            tact.setCheckable(True)
            tact.setChecked(abs(cur_timer - t_sec) < 1)
            tact.triggered.connect(lambda checked, s=t_sec: self._set_timer_duration(s, timer_menu))

        timer_menu.addSeparator()
        pause_act = timer_menu.addAction("⏸ Pause Countdown (Hold Debrief)")
        pause_act.setCheckable(True)
        pause_act.setChecked(self.window.report_timer_paused)
        pause_act.triggered.connect(lambda checked: self._toggle_timer_pause(pause_act))

        menu.addSeparator()

        # Display Mode Submenu
        mode_menu = menu.addMenu("Display Mode")
        current_mode = self.config_mgr.get("mode", "wallpaper")
        
        m_wall = mode_menu.addAction("Wallpaper Layer (Behind Apps)")
        m_wall.setCheckable(True)
        m_wall.setChecked(current_mode == "wallpaper")
        m_wall.triggered.connect(lambda: self._set_mode("wallpaper", m_wall, m_over))

        m_over = mode_menu.addAction("Overlay HUD (Always on Top)")
        m_over.setCheckable(True)
        m_over.setChecked(current_mode == "overlay")
        m_over.triggered.connect(lambda: self._set_mode("overlay", m_wall, m_over))

        # Screen Position Submenu
        pos_menu = menu.addMenu("Screen Position")
        cur_pos = self.config_mgr.get("screen_position", "right_half")
        positions = [
            ("right_half", "Right Half of Screen (Default)"),
            ("fullscreen", "Full Screen"),
            ("left_half", "Left Half of Screen")
        ]
        for p_key, p_name in positions:
            pact = pos_menu.addAction(p_name)
            pact.setCheckable(True)
            pact.setChecked(cur_pos == p_key)
            pact.triggered.connect(lambda checked, k=p_key: self._set_position(k, pos_menu))

        # Click-Through Toggle
        ct_action = menu.addAction("Click-Through Enabled")
        ct_action.setCheckable(True)
        ct_action.setChecked(self.config_mgr.get("click_through", True))
        ct_action.triggered.connect(lambda checked: self.window.set_click_through(checked))

        # Panel Backdrop Toggle
        glass_act = menu.addAction("Panel Cyber Glass (High Contrast)")
        glass_act.setCheckable(True)
        glass_act.setChecked(self.config_mgr.get("panel_backdrop", True))
        glass_act.triggered.connect(lambda checked: self.window.set_panel_backdrop(checked))

        menu.addSeparator()

        # Theme Selector Submenu
        theme_menu = menu.addMenu("Color Theme")
        cur_theme = self.config_mgr.get("theme", "cyber_neon")
        for key, t_data in THEMES.items():
            act = theme_menu.addAction(t_data["name"])
            act.setCheckable(True)
            act.setChecked(cur_theme == key)
            act.triggered.connect(lambda checked, k=key: self._set_theme(k, theme_menu))

        # Layout Selector Submenu
        layout_menu = menu.addMenu("HUD Layout")
        cur_layout = self.config_mgr.get("layout", "dual_wing")
        layouts = [
            ("dual_wing", "Dual Wing (Recommended)"),
            ("right_hud", "Right Wing Only"),
            ("left_hud", "Left Wing Only")
        ]
        for l_key, l_name in layouts:
            lact = layout_menu.addAction(l_name)
            lact.setCheckable(True)
            lact.setChecked(cur_layout == l_key)
            lact.triggered.connect(lambda checked, k=l_key: self._set_layout(k, layout_menu))

        # Opacity Submenu
        opacity_menu = menu.addMenu("HUD Opacity")
        cur_op = float(self.config_mgr.get("opacity", 0.90))
        opacities = [(1.0, "100% Vibrant"), (0.90, "90% Default"), (0.75, "75% Soft"), (0.50, "50% Translucent"), (0.35, "35% Ghost Layer")]
        for op_val, op_lbl in opacities:
            oact = opacity_menu.addAction(op_lbl)
            oact.setCheckable(True)
            oact.setChecked(abs(cur_op - op_val) < 0.05)
            oact.triggered.connect(lambda checked, val=op_val: self._set_opacity(val, opacity_menu))

        # Animation Speed (FPS) Submenu
        fps_menu = menu.addMenu("Animation Refresh Rate")
        cur_fps = int(self.config_mgr.get("fps", 30))
        fps_opts = [(60, "60 FPS (Ultra Smooth)"), (30, "30 FPS (Smooth)"), (20, "20 FPS (Balanced)"), (10, "10 FPS (Eco Mode)")]
        for f_val, f_lbl in fps_opts:
            fact = fps_menu.addAction(f_lbl)
            fact.setCheckable(True)
            fact.setChecked(cur_fps == f_val)
            fact.triggered.connect(lambda checked, val=f_val: self._set_fps(val, fps_menu))

        menu.addSeparator()

        # Feature Toggles
        avatar_act = menu.addAction("Cyber AI Sentinel Mascot Avatar")
        avatar_act.setCheckable(True)
        avatar_act.setChecked(self.config_mgr.get("agent_avatar_enabled", True))
        avatar_act.triggered.connect(self._toggle_avatar)

        wave_act = menu.addAction("Dynamic Neural Waveform")
        wave_act.setCheckable(True)
        wave_act.setChecked(self.config_mgr.get("agent_neural_wave_enabled", True))
        wave_act.triggered.connect(self._toggle_wave)

        ambient_act = menu.addAction("Ambient Margin Streams")
        ambient_act.setCheckable(True)
        ambient_act.setChecked(self.config_mgr.get("show_ambient_stream", True))
        ambient_act.triggered.connect(self._toggle_ambient)

        cores_act = menu.addAction("20-Core CPU Micro-Grid")
        cores_act.setCheckable(True)
        cores_act.setChecked(self.config_mgr.get("show_per_core_matrix", True))
        cores_act.triggered.connect(self._toggle_cores)

        menu.addSeparator()

        # Exit
        exit_action = menu.addAction("Exit Agent")
        exit_action.triggered.connect(self._exit_app)

        self.tray.setContextMenu(menu)

    def _switch_hud_view(self, view_idx: int, v_tel: QAction, v_game: QAction):
        v_tel.setChecked(view_idx == 0)
        v_game.setChecked(view_idx == 1)
        self.window.switch_to_view(view_idx)

    def _trigger_simulated_game(self):
        """Simulates a completed game session and triggers animated HUD transition."""
        self.agent.simulate_game_session()
        self.window.switch_to_view(1)

    def _start_manual_game(self):
        success = self.agent.start_manual_game_tracking()
        if success:
            self.tray.showMessage("Sentinel Game Tracker", "Tracking active window as game session...", QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            self.tray.showMessage("Sentinel Game Tracker", "Could not identify active foreground window.", QSystemTrayIcon.MessageIcon.Warning, 2000)

    def _stop_manual_game(self):
        report = self.agent.stop_manual_game_tracking()
        if report:
            self.window.switch_to_view(1)
        else:
            self.tray.showMessage("Sentinel Game Tracker", "No active game session was running.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def _set_mode(self, mode: str, wall_act: QAction, over_act: QAction):
        wall_act.setChecked(mode == "wallpaper")
        over_act.setChecked(mode == "overlay")
        self.window.set_display_mode(mode)

    def _set_position(self, pos: str, pos_menu: QMenu):
        for act in pos_menu.actions():
            act.setChecked(False)
        self.window.set_screen_position(pos)

    def _set_theme(self, theme_key: str, theme_menu: QMenu):
        for act in theme_menu.actions():
            act.setChecked(False)
        self.window.set_theme(theme_key)
        # Update tray icon color
        color_hex = THEMES[theme_key]["primary"].name()
        self.pixmap = create_tray_pixmap(color_hex)
        self.tray.setIcon(QIcon(self.pixmap))

    def _set_layout(self, layout_key: str, layout_menu: QMenu):
        for act in layout_menu.actions():
            act.setChecked(False)
        self.window.set_layout(layout_key)

    def _set_opacity(self, val: float, opacity_menu: QMenu):
        for act in opacity_menu.actions():
            act.setChecked(False)
        self.window.set_opacity(val)

    def _set_fps(self, val: int, fps_menu: QMenu):
        for act in fps_menu.actions():
            act.setChecked(False)
        self.window.set_fps(val)

    def _toggle_ambient(self, checked: bool):
        self.config_mgr.set("show_ambient_stream", checked)
        self.window.update()

    def _toggle_cores(self, checked: bool):
        self.config_mgr.set("show_per_core_matrix", checked)
        self.window.update()

    def _set_timer_duration(self, sec: float, timer_menu: QMenu):
        for act in timer_menu.actions():
            if act.isCheckable() and "Pause" not in act.text():
                act.setChecked(False)
        self.window.set_report_timer_duration(sec)

    def _toggle_timer_pause(self, pause_act: QAction):
        self.window.toggle_report_timer_pause()
        pause_act.setChecked(self.window.report_timer_paused)

    def _toggle_avatar(self, checked: bool):
        self.config_mgr.set("agent_avatar_enabled", checked)
        self.window.update()

    def _toggle_wave(self, checked: bool):
        self.config_mgr.set("agent_neural_wave_enabled", checked)
        self.window.update()

    def _exit_app(self):
        self.agent.stop()
        QApplication.quit()
