"""
PC Monitoring Agent & Animated Desktop Wallpaper HUD
Main Application Entry Point.
"""

import sys
import os
import signal
import argparse

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.config_manager import ConfigManager
from core.system_agent import SystemAgent
from ui.wallpaper_window import WallpaperWindow
from ui.tray_icon import SystemTrayController

def parse_args():
    parser = argparse.ArgumentParser(description="PC Monitoring Agent & Animated Wallpaper HUD")
    parser.add_argument("--theme", choices=["cyber_neon", "matrix_protocol", "amber_crt", "blood_red", "ghost_white", "synthwave"], help="Initial color theme")
    parser.add_argument("--layout", choices=["dual_wing", "right_hud", "left_hud"], help="HUD layout preset")
    parser.add_argument("--mode", choices=["wallpaper", "overlay"], help="Display mode (wallpaper layer or overlay on top)")
    parser.add_argument("--position", choices=["right_half", "fullscreen", "left_half"], help="Screen position (right_half, fullscreen, left_half)")
    parser.add_argument("--opacity", type=float, help="HUD opacity from 0.2 to 1.0")
    parser.add_argument("--fps", type=int, choices=[10, 20, 30, 60], help="Animation refresh rate")
    parser.add_argument("--no-click-through", action="store_true", help="Disable click-through (allows mouse clicks)")
    return parser.parse_args()

def main():
    # Allow clean exit on Ctrl+C from console
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Enable High-DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load configuration
    config_mgr = ConfigManager("config.json")
    args = parse_args()
    
    if args.theme:
        config_mgr.set("theme", args.theme)
    if args.layout:
        config_mgr.set("layout", args.layout)
    if args.mode:
        config_mgr.set("mode", args.mode)
    if args.position:
        config_mgr.set("screen_position", args.position)
    if args.opacity is not None:
        config_mgr.set("opacity", max(0.1, min(1.0, args.opacity)))
    if args.fps:
        config_mgr.set("fps", args.fps)
    if args.no_click_through:
        config_mgr.set("click_through", False)

    # Initialize System Monitoring Agent
    agent = SystemAgent(
        sample_interval=float(config_mgr.get("sample_interval", 1.0)),
        history_length=int(config_mgr.get("history_points", 45)),
        custom_games=config_mgr.get("custom_games", [])
    )
    agent.start()

    # Create Transparent Wallpaper Window
    window = WallpaperWindow(agent, config_mgr)
    window.show()

    # Create Windows Notification Tray Controller
    tray = SystemTrayController(window, agent, config_mgr)

    print("==================================================================")
    print(" ◈ PC MONITORING AGENT // ANIMATED WALLPAPER HUD ONLINE ◈")
    print(f" Theme     : {config_mgr.get('theme')}")
    print(f" Position  : {config_mgr.get('screen_position')} (right half of screen)")
    print(f" Mode      : {config_mgr.get('mode')} (transparent desktop wallpaper layer)")
    print(f" Layout    : {config_mgr.get('layout')}")
    print(f" Click-thru: {config_mgr.get('click_through')}")
    print(" Access controls & themes anytime via the Windows System Tray icon.")
    print("==================================================================")

    exit_code = app.exec()
    agent.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
