# ◈ Sentinel PC Monitoring Agent & Animated Wallpaper HUD

An autonomous PC hardware monitoring agent that renders its dashboard as a **live, animated, transparent text-based HUD layer directly on top of your static Windows desktop wallpaper**.

Your existing static wallpaper remains 100% visible beneath it, your desktop icons remain fully clickable through the HUD, and all telemetry updates with high-tech monospace typography, glowing drop-shadows, and smooth cyberpunk animations.

---

## ⚡ Highlights & Capabilities

- **Cyber AI Sentinel Mascot Avatar & Live Animation**: A dedicated 5-line animated cyber robotic avatar console with rotating orbital gyroscopes, animated eye blinks and glances, sweeping combat tactical laser scan bar during gaming, and dynamic vocoder speech equalizer.
- **Real-Time Reactive Neural Oscilloscope**: A fluid mathematical harmonic waveform (`SPARK_CHARS`) that dynamically reacts to combined CPU + GPU workload—calm breathing sine wave at idle, electric high-frequency jitter at peak gaming loads.
- **Debrief Auto-Revert Countdown Timer**: Post-game report HUD automatically counts down (default: 2.5 minutes / 150s) and slides smoothly back to Live Telemetry HUD, with pause and duration controls in tray menu and hotkey `T` instant return.
- **Right-Half Transparent Desktop Layer**: Specifically occupies the right half of your screen (`x = 960` to `1920` on 1080p). The left half of your screen (where desktop icons and primary wallpaper subjects sit) is completely open and untouched!
- **Crystal-Clear Typography (Zero Distortion)**: Powered by `Cascadia Code` (built into Windows 11) with 100% uniform character metrics (every letter, box line, and sparkline block has identical 8px width). Eliminates blurred multi-pass glow fringes and misalignment.
- **Translucent Cyber Glass Panels**: Sleek semi-transparent dark glass backings behind each module provide 100% sharp contrast against any wallpaper (including bright skies and colorful backgrounds) while keeping the wallpaper fully visible.
- **Click-Through Desktop Integration**: Mouse clicks pass directly through to your desktop shortcuts, folders, and icons via Windows API layered transparency (`WS_EX_TRANSPARENT | WS_EX_LAYERED`).
- **Autonomous Monitoring Agent**: Runs in the background, continuously collecting hardware metrics and generating real-time diagnostic insights, anomaly detection, and health scores.
- **Real-Time ASCII Sparkline Charts**: 60-second rolling Unicode block graphs (` ▂▃▄▅▆▇█`) for CPU, RAM, GPU, Disk I/O, and Network throughput.
- **20-Core CPU Matrix**: Individual micro-bars for all logical cores alongside overall load and clock frequency.
- **Dedicated GPU Telemetry**: Real-time NVIDIA GPU utilization, VRAM usage, and thermal temperature sensors (e.g. RTX 3060).
- **Multi-Drive Storage & I/O**: Real-time read/write disk delta counters and storage capacity meters across partitions (`C:`, `D:`, `E:`).
- **Process Sentinel**: Live tracking of the top 5 CPU- and memory-consuming processes.
- **Agent Intelligence Stream**: A live terminal log ticker at the bottom with blinking cursor `_` streaming health alerts, thermal headroom, and system events.
- **Windows System Tray Control**: Manage screen positions (`Right Half`, `Full Screen`, `Left Half`), themes, opacity, and toggles directly from your notification area.

---

## 🎨 Built-In Color Themes

| Theme Key | Name | Visual Style |
| :--- | :--- | :--- |
| `cyber_neon` | **Cyber Neon (Default)** | Electric Cyan (`#00f0ff`) + Neon Pink (`#ff007f`) with ice-blue glow |
| `matrix_protocol` | **Matrix Protocol** | Phosphor Terminal Green (`#00ff66`) + Lime Emerald (`#50fa7b`) |
| `amber_crt` | **Amber CRT** | Retro Mainframe VT220 Amber (`#ffb000`) + Solar Gold |
| `blood_red` | **Apex Crimson** | Tactical Red (`#ff3246`) + Blaze Orange (`#ff8000`) |
| `ghost_white` | **Ghost Silver** | Minimalist Crisp White (`#f5f8fa`) + Sky Slate Cyan |
| `synthwave` | **Outrun Synthwave** | Neon Violet (`#c36eff`) + Hot Magenta (`#ff5ab4`) |

---

## 📐 Layout Presets

1. **Dual Wing HUD (`dual_wing` - Recommended)**:
   - **Left Wing**: CPU overall + 20-core micro-grid, RAM, Swap, and NVIDIA GPU telemetry.
   - **Right Wing**: Multi-drive storage, Disk I/O, Network ingress/egress, and Top 5 Processes.
   - **Top Center**: Live digital clock, date, host info, uptime, and system health status.
   - **Bottom Center**: Autonomous Agent intelligence log ticker with typewriter/fade animation.
   - **Center Screen**: Completely open to keep your wallpaper subject clear and unobstructed!
2. **Right Wing HUD (`right_hud`)**:
   - Consolidates all panels into a sleek 540px sidebar on the right edge of your screen. Perfect if your desktop icons are arranged on the left!
3. **Left Wing HUD (`left_hud`)**:
   - Consolidates all panels onto the left edge of your screen.

---

## 🚀 Quick Start & Launching

### Method 1: Double-Click Launcher (Standard)
Double-click:
```
run_wallpaper_agent.bat
```
This starts the monitoring agent with a console window showing initialization telemetry.

### Method 2: Silent Background Launcher (No Console Window)
Double-click:
```
run_silent.vbs
```
This runs the application silently in the background using `pythonw.exe`. The HUD will appear on your desktop without any command prompt window.

### Method 3: Command Line with Custom Options
You can launch with custom arguments:
```powershell
python main.py --theme matrix_protocol --layout dual_wing --opacity 0.85 --fps 30
```

Available flags:
- `--position`: `right_half` (Default), `fullscreen`, `left_half`
- `--theme`: `cyber_neon`, `matrix_protocol`, `amber_crt`, `blood_red`, `ghost_white`, `synthwave`
- `--layout`: `dual_wing`, `right_hud`, `left_hud`
- `--mode`: `wallpaper` (pinned behind open apps) or `overlay` (always floating on top)
- `--opacity`: Value between `0.2` and `1.0` (default: `0.95`)
- `--fps`: `10`, `20`, `30`, `60` (default: `30`)
- `--no-click-through`: Disables click-through for testing or interactive manipulation

---

## ⚙️ Configuration (`config.json`)

All settings are stored in `config.json` and persist across launches. You can also change them on-the-fly from the Windows System Tray menu:

```json
{
    "theme": "cyber_neon",
    "layout": "dual_wing",
    "mode": "wallpaper",
    "opacity": 0.9,
    "fps": 30,
    "sample_interval": 1.0,
    "click_through": true,
    "font_family": "Consolas",
    "font_size": 11,
    "show_ambient_stream": true,
    "show_per_core_matrix": true,
    "history_points": 45
}
```

---

## 🎮 Game Session Monitoring & Animated Debrief HUD

The Agent features an autonomous **Game Activity Sentinel** that automatically monitors your PC during gameplay and morphs your HUD when you finish:

1. **Automatic Game Launch Detection**:
   - Detects when you launch games from Steam, Epic Games, Riot, Battle.net, GOG, or direct executables (`Cyberpunk2077.exe`, `cs2.exe`, `dota2.exe`, `valorant.exe`, `eldenring.exe`, etc.).
2. **Whole-PC Gameplay Surveillance**:
   - Tracks session play time, average & peak GPU utilization, RTX 3060 VRAM consumption, thermal headroom, CPU thread loads, and disk asset streaming spikes.
   - Detects thermal anomalies, frame drop bottlenecks, and asset streaming bursts.
3. **Automatic Post-Game Debrief HUD with Auto-Revert Timer**:
   - The moment you close your game, the desktop HUD **smoothly slides with an animated cyber transition** from the Live Telemetry HUD into the **Game Performance Debrief HUD**!
   - Shows performance grades (`Grade S`, `A`, `B`, `C`), AI Agent hardware verdict, session timeline events, and GPU/CPU session curves.
   - **Auto-Revert Countdown**: Displays a live timer: `[ AUTO-RETURNING IN 02:24 ]`. After 2.5 minutes (configurable to 1 min, 5 min, or manual), it smoothly slides back to the Live Telemetry HUD automatically!
   - **Hold / Pause Debrief**: Want more time to read? Right-click the tray icon -> `Debrief Auto-Return Timer` -> `⏸ Pause Countdown (Hold Debrief)` to inspect your stats as long as you like.
4. **Switching Views Back & Forth**:
   - **Hotkey**: Press `T` anytime to toggle between Live Telemetry HUD and Game Report HUD (or return immediately without waiting for timer).
   - **System Tray**: Right-click the tray icon -> `Active HUD View` to choose which HUD is displayed.
   - **Test / Simulation**: Click `⚡ Simulate Game Report (Test Animation)` in the tray menu to test the animated transition and countdown immediately without launching a game.

---

## 🖥️ System Tray Controls

Look for the glowing cyan core icon in your Windows Taskbar Notification Area (bottom right). Right-clicking opens:

- **Active HUD View**: Smoothly switch between `Live System Telemetry HUD` and `Game Performance Report HUD`.
- **⚡ Simulate Game Report**: Instantly triggers a test game debrief with smooth slide animation.
- **Display Mode**: Switch between `Wallpaper Layer` (stays behind apps) and `Overlay HUD` (always on top).
- **Screen Position**: Toggle between `Right Half of Screen (Default)`, `Full Screen`, and `Left Half`.
- **Panel Cyber Glass**: Toggle high-contrast translucent dark glass backing.
- **Click-Through**: Toggle click-through on/off.
- **Color Theme**: Switch instantly between all 6 color palettes.
- **HUD Opacity**: Change opacity (100% Vibrant, 90%, 75%, 50%, 35% Ghost Layer).
- **Exit Agent**: Clean shutdown of background threads and window.
