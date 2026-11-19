"""
Automated Verification Suite for:
1. Auto-Revert Debrief Countdown Timer (2-3 min auto-dismiss back to live telemetry)
2. Cyber AI Sentinel Mascot Avatar & Live Reactive Neural Oscilloscope Waveform
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt

from core.config_manager import ConfigManager
from core.system_agent import SystemAgent
from ui.themes import get_theme
from ui.ascii_art import render_neural_wave, get_mascot_segments
from ui.hud_painter import HUDPainter
from ui.wallpaper_window import WallpaperWindow

def main():
    print("=== STARTING COMPREHENSIVE V2 FEATURE VERIFICATION ===")
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Test Config defaults
    print("\n[TEST 1] Verifying Config Manager defaults...")
    cfg = ConfigManager("config.json")
    dismiss_sec = cfg.get("game_report_auto_dismiss_sec")
    avatar_enabled = cfg.get("agent_avatar_enabled")
    wave_enabled = cfg.get("agent_neural_wave_enabled")
    print(f"  game_report_auto_dismiss_sec: {dismiss_sec}s")
    print(f"  agent_avatar_enabled: {avatar_enabled}")
    print(f"  agent_neural_wave_enabled: {wave_enabled}")
    assert dismiss_sec == 150, f"Expected 150, got {dismiss_sec}"
    assert avatar_enabled is True
    assert wave_enabled is True
    print("  -> Config verification PASSED!")

    # 2. Test ASCII Mascot and Waveform
    print("\n[TEST 2] Verifying ASCII Mascot Avatar & Waveform geometry...")
    for load in [0.0, 15.0, 50.0, 85.0, 100.0]:
        wave = render_neural_wave(tick=10, load=load, width=28)
        assert len(wave) == 28, f"Wave length mismatch: {len(wave)} != 28"
    print("  -> Waveform width 100% verified across loads.")

    for mode in ["normal", "game", "high"]:
        for t in range(50):
            rows = get_mascot_segments(t, mode=mode, load=80.0 if mode == "high" else 20.0)
            assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"
            for r_idx, r in enumerate(rows):
                total_w = sum(len(text) for text, _ in r)
                assert total_w == 20, f"Mascot row {r_idx} len {total_w} != 20 on tick {t}, mode {mode}"
    print("  -> 5-row Cyber Mascot 100% verified at exact 20 characters across all animation states.")

    # 3. Test Agent state and thoughts
    print("\n[TEST 3] Verifying System Agent dynamic cognition and snapshot...")
    agent = SystemAgent(sample_interval=0.2)
    agent.start()
    time.sleep(0.5)
    
    snap = agent.get_snapshot()
    assert snap is not None
    assert "agent_mood" in snap
    assert "agent_thought" in snap
    assert "diagnostic_cycle" in snap
    print(f"  Agent Mood: {snap['agent_mood']}")
    print(f"  Agent Thought: {snap['agent_thought']}")
    print("  -> System Agent cognitive snapshot PASSED!")

    # 4. Test HUD Painter with Agent Console & Game Debrief
    print("\n[TEST 4] Verifying QPainter rendering with Agent Mascot & Timer...")
    painter_engine = HUDPainter(cfg)
    theme = get_theme("cyber_neon")
    pix = QPixmap(960, 1080)
    pix.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pix)
    # Render Telemetry HUD (with Agent Mascot & Neural Console)
    painter_engine.paint(
        painter, 960, 1080, snap, tick=1, theme=theme,
        view_mode=0, transition_progress=0.0
    )
    print("  -> Telemetry HUD with Mascot & Neural Core rendered successfully.")

    # Simulate game session
    print("  Simulating game session...")
    sim_report = agent.simulate_game_session()
    snap = agent.get_snapshot()
    assert snap.get("game_report") is not None

    # Render Game Debrief HUD with active 150s countdown timer
    painter_engine.paint(
        painter, 960, 1080, snap, tick=2, theme=theme,
        view_mode=1, transition_progress=1.0,
        report_countdown_sec=148.5, report_timer_paused=False
    )
    print("  -> Game Debrief HUD with active countdown timer rendered successfully.")

    # Render Game Debrief HUD with paused countdown
    painter_engine.paint(
        painter, 960, 1080, snap, tick=3, theme=theme,
        view_mode=1, transition_progress=1.0,
        report_countdown_sec=120.0, report_timer_paused=True
    )
    print("  -> Game Debrief HUD with paused timer rendered successfully.")

    # Render Slide transition frame
    painter_engine.paint(
        painter, 960, 1080, snap, tick=4, theme=theme,
        view_mode=0, transition_progress=0.5,
        report_countdown_sec=145.0, report_timer_paused=False
    )
    print("  -> Slide transition frame rendered successfully.")
    painter.end()

    # 5. Test WallpaperWindow Auto-Dismiss Logic
    print("\n[TEST 5] Verifying WallpaperWindow countdown & auto-revert...")
    agent.clear_new_game_report_flag()
    win = WallpaperWindow(agent, cfg)
    
    # Switch to view 1 (Game Report HUD) with countdown
    win.switch_to_view(1, auto_countdown=True)
    assert win.transition_target == 1.0
    assert win.report_countdown_sec == 150.0
    assert win.report_timer_paused is False
    print(f"  Switched to Game Debrief HUD: countdown armed at {win.report_countdown_sec}s")

    # Fast-forward timer to 0.01s (less than 1 frame dt of 1/60s)
    win.report_countdown_sec = 0.01
    win.view_mode = 1
    # Trigger one animation frame
    win._on_animation_frame()
    
    print(f"  After timer expired: report_countdown_sec={win.report_countdown_sec}, transition_target={win.transition_target}")
    assert win.report_countdown_sec == 0.0
    assert win.transition_target == 0.0, f"Expected transition back to 0.0, got {win.transition_target}"
    print("  -> Auto-revert countdown successfully triggered transition back to Telemetry HUD!")

    # Test pause
    win.switch_to_view(1, auto_countdown=True)
    win.toggle_report_timer_pause()
    assert win.report_timer_paused is True
    initial_sec = win.report_countdown_sec
    win._on_animation_frame()
    assert win.report_countdown_sec == initial_sec, "Timer decremented while paused!"
    print("  -> Pause countdown functionality PASSED!")

    # Cleanup
    agent.stop()
    win.close()
    print("\n=== ALL TESTS PASSED WITH 100% SUCCESS! ===")

if __name__ == "__main__":
    main()
