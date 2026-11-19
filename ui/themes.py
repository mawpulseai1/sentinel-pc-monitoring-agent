"""
Color Themes for Animated Text-Based Desktop Wallpaper HUD.
Curated for maximum readability, luminescence, and cyber/terminal aesthetics.
"""

from typing import Dict, Any
from PySide6.QtGui import QColor

THEMES: Dict[str, Dict[str, Any]] = {
    "cyber_neon": {
        "name": "Cyber Neon (Cyan / Magenta)",
        "primary": QColor(0, 240, 255),       # #00f0ff
        "secondary": QColor(0, 160, 220),     # #00a0dc
        "accent": QColor(255, 0, 127),        # #ff007f Neon Pink
        "dim": QColor(0, 80, 120, 140),       # Translucent cyan-blue
        "glow": QColor(0, 240, 255, 70),      # Cyan glow
        "danger": QColor(255, 40, 80),        # High alert red
        "success": QColor(50, 255, 120),      # #32ff78
        "ambient": QColor(0, 180, 220, 45)    # Very faint ambient stream
    },
    "matrix_protocol": {
        "name": "Matrix Protocol (Emerald Green)",
        "primary": QColor(0, 255, 102),       # #00ff66
        "secondary": QColor(0, 180, 75),      # #00b44b
        "accent": QColor(180, 255, 50),       # Lime accent
        "dim": QColor(0, 80, 30, 150),        # Translucent green
        "glow": QColor(0, 255, 102, 75),      # Green phosphor glow
        "danger": QColor(255, 60, 60),        # Danger red
        "success": QColor(80, 255, 120),
        "ambient": QColor(0, 200, 80, 45)
    },
    "amber_crt": {
        "name": "Amber CRT (Mainframe / VT220)",
        "primary": QColor(255, 176, 0),       # #ffb000
        "secondary": QColor(200, 130, 0),     # #c88200
        "accent": QColor(255, 225, 60),       # Yellow highlight
        "dim": QColor(100, 60, 0, 140),       # Dark amber
        "glow": QColor(255, 176, 0, 75),      # Amber bloom
        "danger": QColor(255, 70, 40),
        "success": QColor(255, 200, 50),
        "ambient": QColor(200, 130, 0, 45)
    },
    "blood_red": {
        "name": "Apex Crimson (Combat / Tactical)",
        "primary": QColor(255, 50, 70),       # #ff3246
        "secondary": QColor(190, 35, 50),     # #be2332
        "accent": QColor(255, 130, 0),        # Blaze orange
        "dim": QColor(100, 20, 30, 140),
        "glow": QColor(255, 50, 70, 75),
        "danger": QColor(255, 20, 20),
        "success": QColor(255, 160, 50),
        "ambient": QColor(200, 40, 60, 45)
    },
    "ghost_white": {
        "name": "Ghost Silver (Minimalist Slate)",
        "primary": QColor(245, 248, 250),     # Pure crisp white
        "secondary": QColor(150, 170, 190),   # Cool slate
        "accent": QColor(100, 210, 255),      # Sky cyan accent
        "dim": QColor(80, 95, 110, 140),
        "glow": QColor(200, 225, 255, 60),
        "danger": QColor(255, 75, 90),
        "success": QColor(110, 230, 170),
        "ambient": QColor(180, 200, 220, 40)
    },
    "synthwave": {
        "name": "Outrun Synthwave (Violet / Pink)",
        "primary": QColor(195, 110, 255),     # Violet
        "secondary": QColor(135, 70, 200),
        "accent": QColor(255, 90, 180),       # Hot magenta
        "dim": QColor(80, 30, 120, 140),
        "glow": QColor(195, 110, 255, 75),
        "danger": QColor(255, 50, 100),
        "success": QColor(80, 240, 220),
        "ambient": QColor(170, 80, 230, 45)
    }
}

def get_theme(theme_name: str) -> Dict[str, Any]:
    return THEMES.get(theme_name, THEMES["cyber_neon"])
