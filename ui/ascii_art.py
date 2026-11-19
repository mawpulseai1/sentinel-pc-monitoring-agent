"""
Text-Based & ASCII Art Generator for Transparent HUD Wallpaper.
Provides high-res unicode sparklines, segmented meters, cyber frames, and animated spinners.
"""

import math
from typing import List, Tuple

# Unicode block elements for sparklines
SPARK_CHARS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# Animated spinner glyph sequences
SPINNERS = {
    "braille": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    "radar": ["◐", "◓", "◑", "◒"],
    "diamond": ["◇", "◈", "◆", "◈"],
    "corners": ["◤", "◥", "◢", "◣"],
    "pulse": ["-", "\\", "|", "/"],
    "brackets": ["[ | ]", "[ / ]", "[ - ]", "[ \\ ]"],
    "signal": [" ", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]
}

def render_sparkline(values: List[float], width: int = 24, min_val: float = 0.0, max_val: float = 100.0) -> str:
    """Renders a series of numeric values into an animated Unicode block sparkline."""
    if not values:
        return " " * width
        
    # Take last `width` values
    slice_vals = values[-width:]
    # Pad left if fewer values than width
    if len(slice_vals) < width:
        slice_vals = [min_val] * (width - len(slice_vals)) + list(slice_vals)
        
    range_span = max(max_val - min_val, 0.001)
    chars = []
    for v in slice_vals:
        v_clamped = max(min_val, min(max_val, v))
        norm = (v_clamped - min_val) / range_span
        idx = int(norm * (len(SPARK_CHARS) - 1))
        idx = max(0, min(len(SPARK_CHARS) - 1, idx))
        chars.append(SPARK_CHARS[idx])
        
    return "".join(chars)

def render_progress_bar(percent: float, width: int = 16, style: str = "blocks", shimmer_pos: int = -1) -> str:
    """
    Renders a text-based progress meter with optional animated scanning shimmer cursor.
    """
    pct = max(0.0, min(100.0, percent))
    filled_len = int(round((pct / 100.0) * width))
    empty_len = width - filled_len
    
    if style == "blocks":
        # Filled with █, empty with ░
        bar_chars = ["█"] * filled_len + ["░"] * empty_len
        # Apply shimmering scanning beam if active
        if 0 <= shimmer_pos < len(bar_chars):
            if shimmer_pos < filled_len:
                bar_chars[shimmer_pos] = "▓"
            else:
                bar_chars[shimmer_pos] = "▒"
        return "".join(bar_chars)
    elif style == "cyber":
        bar_chars = ["■"] * filled_len + ["□"] * empty_len
        return "".join(bar_chars)
    elif style == "dashes":
        bar_chars = ["|"] * filled_len + ["."] * empty_len
        return "".join(bar_chars)
    else:
        return "=" * filled_len + " " * empty_len

def get_spinner(spinner_type: str, tick: int) -> str:
    """Returns the spinner glyph for the given animation tick."""
    seq = SPINNERS.get(spinner_type, SPINNERS["braille"])
    return seq[tick % len(seq)]

def format_box_header(title: str, width: int = 42, icon: str = "") -> str:
    """Creates a cyberpunk styled panel header line."""
    prefix = f"┌── [ {icon} {title} ] " if icon else f"┌── [ {title} ] "
    remain = max(0, width - len(prefix) - 1)
    return prefix + ("─" * remain) + "┐"

def format_box_footer(width: int = 42, extra: str = "") -> str:
    """Creates a styled panel footer line matching exact character width."""
    if extra:
        suffix = f" [ {extra} ] ──┘"
        remain = max(0, width - len(suffix) - 2)
        return "└─" + ("─" * remain) + suffix
    remain = max(0, width - 2)
    return "└" + ("─" * remain) + "┘"

def format_box_line(content: str, width: int = 42) -> str:
    """Wraps a content string inside box vertical borders."""
    # Ensure line fits inside borders
    avail = max(0, width - 4)
    padded = content.ljust(avail)
    if len(padded) > avail:
        padded = padded[:avail]
    return f"│ {padded} │"

def render_neural_wave(tick: int, load: float = 20.0, width: int = 32) -> str:
    """
    Generates a fluid real-time mathematical harmonic oscilloscope wave.
    Reacts to live hardware load (CPU+GPU):
    - Low load: gentle, slow, low-amplitude sine wave.
    - High load: fast, dynamic harmonics with electric peaks reaching '█'.
    """
    norm_load = max(0.0, min(100.0, load)) / 100.0
    speed = 0.12 + (norm_load * 0.38)
    freq1 = 0.18 + (norm_load * 0.16)
    freq2 = 0.38 + (norm_load * 0.28)
    amplitude = 0.40 + (norm_load * 0.55)
    
    chars = []
    for i in range(width):
        w1 = math.sin((i * freq1) + (tick * speed))
        w2 = math.cos((i * freq2) - (tick * speed * 1.35))
        combined = (w1 * 0.65 + w2 * 0.35) * amplitude
        norm = (combined + 1.0) / 2.0
        idx = int(norm * 8.99)
        idx = max(0, min(8, idx))
        chars.append(SPARK_CHARS[idx])
    return "".join(chars)

def get_mascot_segments(tick: int, mode: str = "normal", load: float = 10.0) -> List[List[Tuple[str, str]]]:
    """
    Returns the 5 rows of the Animated Cyber AI Sentinel Avatar Mascot.
    Each row is guaranteed to be exactly 20 characters in width.
    Each item is a (text, color_key) tuple where color_key maps to theme palette.
    """
    # 1. Rotating antenna orbital gyroscopes
    gyros = ["◜", "◝", "◞", "◟"]
    g1 = gyros[(tick // 3) % 4]
    g2 = gyros[((tick // 3) + 2) % 4]
    
    r0 = [
        (" ", "dim"),
        (g1, "accent"),
        ("───[", "dim"),
        ("SENTINEL", "primary"),
        ("]───", "dim"),
        (g2, "accent"),
        (" ", "dim")
    ]
    
    # 2. Visor / Ocular scanner
    if mode == "game":
        # Sweeping combat laser bar
        scan_pos = (tick // 2) % 6
        if scan_pos > 3:
            scan_pos = 6 - scan_pos
        laser = ["░"] * 4
        laser[scan_pos] = "█"
        eyes = "".join(laser)
        r1 = [
            ("/", "dim"),
            ("  ◄◄ [ ", "secondary"),
            (eyes, "accent"),
            (" ] ►►  ", "secondary"),
            ("\\", "dim")
        ]
    elif load > 70.0:
        # Alert eyes pulsing
        eyes = "▲ ▲" if (tick % 10 < 5) else "◈ ◈"
        r1 = [
            ("/", "dim"),
            ("  ◄◄ [ ", "danger"),
            (eyes, "danger"),
            (" ] ►►   ", "danger"),
            ("\\", "dim")
        ]
    else:
        # Normal mode with periodic blinking and glances
        phase = tick % 90
        if phase in [86, 87]:
            eyes = "─ ─"
            eye_col = "dim"
        elif phase in [40, 41]:
            eyes = "◐ ◐"
            eye_col = "accent"
        elif phase in [42, 43]:
            eyes = "◑ ◑"
            eye_col = "accent"
        else:
            eyes = "◉ ◉"
            eye_col = "accent"
        r1 = [
            ("/", "dim"),
            ("  ◄◄ [ ", "secondary"),
            (eyes, eye_col),
            (" ] ►►   ", "secondary"),
            ("\\", "dim")
        ]

    # 3. Vocoder speech equalizer mouth
    voc_bars = ["[ █ ▄ ▆ ▃ ]", "[ ▃ █ ▄ ▅ ]", "[ ▆ ▃ █ ▄ ]", "[ ▄ ▆ ▃ █ ]"]
    voc = voc_bars[(tick // 4) % len(voc_bars)]
    r2 = [
        ("│   ", "dim"),
        (voc, "primary"),
        ("    │", "dim")
    ]
    
    # 4. Sensor collar
    r3 = [("\\   ╭─────────╮    /", "dim")]
    
    # 5. Cybernetic base
    r4 = [(" └──┴─────────┴───┘ ", "dim")]
    
    return [r0, r1, r2, r3, r4]
