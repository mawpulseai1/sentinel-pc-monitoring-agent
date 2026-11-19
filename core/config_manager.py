"""
Configuration Manager
Handles loading, defaults, validation, and persistence of user preferences in JSON.
"""

import json
import os
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "theme": "cyber_neon",
    "layout": "dual_wing",
    "screen_position": "right_half", # "right_half", "fullscreen", "left_half"
    "mode": "wallpaper",             # "wallpaper" (at bottom behind apps) or "overlay" (always on top)
    "opacity": 0.95,                 # Text / HUD opacity (0.2 to 1.0)
    "fps": 30,                       # Animation frame rate (10, 20, 30, 60)
    "sample_interval": 1.0,          # Telemetry collection rate (seconds)
    "click_through": True,           # Pass mouse events through to desktop icons
    "font_family": "Cascadia Code",  # Monospace font with 100% uniform Unicode glyph metrics
    "font_size": 10,
    "panel_backdrop": True,          # Translucent dark glass behind boxes for 100% crisp legibility
    "panel_opacity": 0.40,           # Panel glass opacity (0.0 to 0.7)
    "show_ambient_stream": True,     # Subtle cyber coordinates & hex streams in margins
    "show_per_core_matrix": True,    # Show all 20 CPU core load bars
    "history_points": 35,            # Width of sparkline charts
    "custom_games": [],              # Optional user-defined game process names (e.g. ["mygame.exe"])
    "game_report_auto_dismiss_sec": 150, # Auto-return countdown timer in seconds (150s = 2.5 min; 0 = manual only)
    "agent_avatar_enabled": True,    # Show animated cyber mascot avatar and live neural core
    "agent_neural_wave_enabled": True # Show dynamic load-reactive neural oscilloscope
}

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in DEFAULT_CONFIG:
                            self.config[k] = v
            except Exception as e:
                print(f"Failed to load config from {self.config_path}: {e}")
        else:
            self.save()
        return self.config

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config to {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save()
