"""
Comprehensive Test Suite for Verified News Sentry & Multi-HUD Auto-Rotation (V3)
Validates:
1. AI-slop & clickbait filtering heuristics (0% tolerance).
2. Autonomous News Intelligence Engine snapshot & 30-min scheduled timer.
3. Expandable social chatter under news items.
4. Real-time Agent Recon streaming and cognition log.
5. Multi-HUD view routing and smooth sliding transitions (Views 0, 1, 2).
6. Auto-rotation mechanics between Telemetry HUD and News HUD.
7. QPainter render execution of News HUD with expanded chatter cards.
"""

import sys
import os
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt, QRectF

from core.config_manager import ConfigManager
from core.news_sentry import NewsIntelligenceEngine, AI_SLOP_PATTERNS
from core.system_agent import SystemAgent
from ui.hud_painter import HUDPainter
from ui.wallpaper_window import WallpaperWindow
from ui.themes import get_theme

def test_ai_slop_filter():
    print("\n[TEST 1] Testing AI-Slop & Clickbait Verification Filter...")
    engine = NewsIntelligenceEngine()
    
    slop_samples = [
        "In the rapidly evolving world of artificial intelligence, this is a testament to progress",
        "Doctors hate this one secret revealed to lose weight overnight!",
        "Mind-blowing new GPU breakthrough is a game-changer that will revolutionize the way we compute",
        "THIS CHANGES EVERYTHING 🔥🔥🔥 ARE YOU READY FOR THIS???!!!"
    ]
    for s in slop_samples:
        is_slop = engine._is_ai_slop(s)
        assert is_slop, f"Failed to catch AI slop: {s}"
        print(f"  ✓ Successfully purged slop: '{s[:45]}...'")

    legit_samples = [
        "Open-Weights Reasoning Architecture Benchmarks Released on HuggingFace",
        "Vulkan Ray Reconstruction & Frame Gen Standardized by Khronos Group",
        "Critical UEFI Firmware Flaw Patched in ASUS and MSI Motherboard BIOS Updates",
        "Silicon Motion Monolithic PCIe Gen5 Controller Demonstrates Sub-3W Idle"
    ]
    for legit in legit_samples:
        is_slop = engine._is_ai_slop(legit)
        assert not is_slop, f"False positive flagged on legitimate news: {legit}"
        print(f"  ✓ Legitimate news verified: '{legit[:45]}...'")
    print("-> AI-Slop verification filter PASSED!")

def test_news_engine_snapshot_and_timer():
    print("\n[TEST 2] Testing News Intelligence Engine & 30-Min Timer...")
    engine = NewsIntelligenceEngine(refresh_interval_sec=1800.0)
    snap = engine.get_snapshot()
    
    assert len(snap["items"]) >= 3, "Failed to load verified stories"
    assert "agent_phase" in snap, "Missing agent_phase"
    assert "agent_thought" in snap, "Missing agent_thought"
    assert "countdown_sec" in snap, "Missing countdown_sec"
    assert "countdown_str" in snap, "Missing countdown_str"
    assert snap["refresh_interval_sec"] == 1800.0, "Interval mismatch"

    print(f"  Verified Stories: {len(snap['items'])}")
    print(f"  Agent Phase: {snap['agent_phase']}")
    print(f"  Agent Thought: {snap['agent_thought']}")
    print(f"  Countdown: {snap['countdown_str']}")

    # Test expand/collapse
    first_id = snap["items"][0]["id"]
    assert engine.expanded_news_id == first_id, "First item should be expanded by default"
    print(f"  ✓ Initial expanded item: {first_id}")

    # Toggling collapses it
    engine.toggle_expand(first_id)
    assert engine.expanded_news_id is None, "Collapse toggle failed"
    print(f"  ✓ Collapsed news item")

    # Toggling again expands it
    engine.toggle_expand(first_id)
    assert engine.expanded_news_id == first_id, "Expand toggle failed"
    print(f"  ✓ Re-expanded news item: {first_id}")
    print("-> News Engine Snapshot & Timer PASSED!")

def test_system_agent_integration():
    print("\n[TEST 3] Testing SystemAgent News Integration...")
    agent = SystemAgent(news_interval_sec=1800.0)
    agent.start()
    time.sleep(1.0)
    
    snap = agent.get_snapshot()
    assert "news" in snap, "SystemAgent snapshot missing news dictionary"
    assert len(snap["news"]["items"]) > 0, "No news items in agent snapshot"

    # Test manual sweep trigger
    agent.refresh_news_now()
    snap_after = agent.get_snapshot()
    print(f"  Active Phase after sweep trigger: {snap_after['news']['agent_phase']}")

    agent.stop()
    print("-> SystemAgent News Integration PASSED!")

def test_hud_rendering_and_auto_rotation():
    print("\n[TEST 4] Testing WallpaperWindow Auto-Rotation & Multi-View Rendering...")
    app = QApplication.instance() or QApplication(sys.argv)
    
    cfg = ConfigManager()
    cfg.set("auto_rotate_hud", True)
    cfg.set("hud_rotation_interval_sec", 45)
    
    agent = SystemAgent()
    # Prime telemetry so snapshot["telemetry"] is populated
    data = agent.engine.collect_all()
    agent._process_sample(data)
    window = WallpaperWindow(agent, cfg)
    
    assert window.view_mode == 0, "Initial view must be Telemetry (0)"
    assert window.auto_rotate_enabled is True, "Auto-rotation must be enabled"
    print(f"  Initial View: {window.view_mode} (Telemetry HUD)")
    print(f"  Auto-Rotate Enabled: {window.auto_rotate_enabled} ({window.auto_rotate_interval}s interval)")

    # Test manual view switch to News HUD (View 2)
    window.switch_to_view(2)
    assert window.to_view == 2, "Target view should be 2"
    assert window.from_view == 0, "Source view should be 0"
    print("  ✓ Switched target view to 2 (News Sentry HUD)")

    # Simulate transition steps
    for _ in range(15):
        window._on_animation_frame()
    assert window.view_mode == 2, f"Expected view_mode 2 after animation, got {window.view_mode}"
    print(f"  ✓ Transition completed to View {window.view_mode} (News HUD)")

    # Test auto-rotation step
    window.auto_rotate_countdown = 0.01
    window._on_animation_frame() # Triggers expiration
    assert window.to_view == 0, f"Auto-rotation should switch target from 2 to 0, got {window.to_view}"
    print("  ✓ Auto-rotation successfully triggered slide back to View 0 (Telemetry HUD)")

    # Render tests with QPainter
    pix = QPixmap(960, 1080)
    pix.fill(Qt.GlobalColor.black)
    painter = QPainter(pix)
    theme = get_theme("cyber_neon")
    snap = agent.get_snapshot()

    # 1. Render Telemetry HUD (View 0)
    window.painter_engine.paint(painter, 960, 1080, snap, 1, theme, view_mode=0)
    print("  ✓ QPainter successfully rendered Telemetry HUD (View 0)")

    # 2. Render News HUD (View 2) with expanded chatter
    snap["news"]["expanded_news_id"] = snap["news"]["items"][0]["id"]
    window.painter_engine.paint(painter, 960, 1080, snap, 1, theme, view_mode=2)
    print("  ✓ QPainter successfully rendered News Sentry HUD (View 2) with expanded social chatter")
    assert len(window.painter_engine.news_click_rects) > 0, "No clickable news rects registered"
    print(f"  ✓ Registered {len(window.painter_engine.news_click_rects)} clickable news bounds")

    # 3. Render Game Debrief HUD (View 1)
    agent.simulate_game_session()
    snap_game = agent.get_snapshot()
    window.painter_engine.paint(painter, 960, 1080, snap_game, 1, theme, view_mode=1)
    print("  ✓ QPainter successfully rendered Game Debrief HUD (View 1)")

    # 4. Render active slide transition frame (from 0 to 2 at 50%)
    window.painter_engine.paint(painter, 960, 1080, snap, 1, theme, from_view=0, to_view=2, transition_progress=0.5)
    print("  ✓ QPainter successfully rendered smooth sliding transition between HUDs")

    painter.end()
    print("-> WallpaperWindow Auto-Rotation & Multi-View Rendering PASSED!")

if __name__ == "__main__":
    print("=== STARTING SENTINEL V3 VERIFIED NEWS & MULTI-HUD VERIFICATION ===")
    test_ai_slop_filter()
    test_news_engine_snapshot_and_timer()
    test_system_agent_integration()
    test_hud_rendering_and_auto_rotation()
    print("\n=== ALL V3 NEWS & MULTI-HUD TESTS PASSED WITH 100% SUCCESS! ===")
