"""
Game Activity Monitor & Session Performance Profiler (High-Speed & Non-Blocking)
Detects game launch through multi-layer detection:
1. Active foreground window detection (instant, zero-permission issues).
2. Comprehensive 100+ game executable database.
3. Unreal / Unity / Game engine naming patterns.
4. User-configured custom game processes.
5. Manual start/stop triggers via System Tray.
"""

import time
import os
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List, Optional, Callable
import psutil

user32 = ctypes.windll.user32

# Comprehensive database of popular PC game executables
KNOWN_GAME_EXES = {
    # Valve & Source
    "cs2.exe": "Counter-Strike 2",
    "csgo.exe": "CS:GO",
    "dota2.exe": "Dota 2",
    "tf2.exe": "Team Fortress 2",
    "left4dead2.exe": "Left 4 Dead 2",
    "portal2.exe": "Portal 2",
    "hl2.exe": "Half-Life 2",

    # Riot Games
    "valorant.exe": "Valorant",
    "valorant-win64-shipping.exe": "Valorant",
    "leagueclient.exe": "League of Legends",
    "league of legends.exe": "League of Legends",

    # Epic Games
    "fortniteclient-win64-shipping.exe": "Fortnite",
    "rocketleague.exe": "Rocket League",
    "fallguys_client.exe": "Fall Guys",

    # Blizzard
    "overwatch.exe": "Overwatch 2",
    "diablo iv.exe": "Diablo IV",
    "wow.exe": "World of Warcraft",
    "hearthstone.exe": "Hearthstone",
    "heroes.exe": "Heroes of the Storm",

    # EA
    "apex.exe": "Apex Legends",
    "r5apex.exe": "Apex Legends",
    "fc24.exe": "EA Sports FC 24",
    "fc25.exe": "EA Sports FC 25",
    "fifa23.exe": "FIFA 23",
    "bf2042.exe": "Battlefield 2042",
    "bfv.exe": "Battlefield V",
    "needforspeed.exe": "Need for Speed",
    "nfsunbound.exe": "NFS Unbound",
    "ts4_x64.exe": "The Sims 4",

    # CD Projekt / FromSoftware / Bethesda
    "cyberpunk2077.exe": "Cyberpunk 2077",
    "witcher3.exe": "The Witcher 3",
    "eldenring.exe": "Elden Ring",
    "darksoulsiii.exe": "Dark Souls III",
    "armoredcore6.exe": "Armored Core VI",
    "starfield.exe": "Starfield",
    "skyrimse.exe": "Skyrim Special Edition",
    "fallout4.exe": "Fallout 4",

    # Rockstar
    "gta5.exe": "Grand Theft Auto V",
    "playgtav.exe": "GTA V",
    "gta5_enhanced.exe": "Grand Theft Auto V (Enhanced)",
    "gta5_enhanced_be.exe": "Grand Theft Auto V (Enhanced)",
    "rdr2.exe": "Red Dead Redemption 2",

    # Capcom / Square Enix
    "monsterhunterworld.exe": "Monster Hunter: World",
    "monsterhunterrise.exe": "Monster Hunter Rise",
    "re2.exe": "Resident Evil 2",
    "re4.exe": "Resident Evil 4",
    "ffxvi.exe": "Final Fantasy XVI",
    "ff7remake_.exe": "Final Fantasy VII Remake",

    # Larian / Modern RPGs
    "bg3.exe": "Baldur's Gate 3",
    "bg3_dx11.exe": "Baldur's Gate 3",
    "b1-win64-shipping.exe": "Black Myth: Wukong",
    "helldivers2.exe": "Helldivers 2",
    "palworld.exe": "Palworld",
    "palworld-win64-shipping.exe": "Palworld",
    "forzahorizon5.exe": "Forza Horizon 5",
    "forzahorizon4.exe": "Forza Horizon 4",

    # Hoyoverse
    "genshinimpact.exe": "Genshin Impact",
    "starrail.exe": "Honkai: Star Rail",
    "zenlesszonezero.exe": "Zenless Zone Zero",

    # Sandbox / Survival / Competitive
    "javaw.exe": "Minecraft",
    "minecraft.exe": "Minecraft",
    "minecraft.windows.exe": "Minecraft Bedrock",
    "robloxplayerbeta.exe": "Roblox",
    "rustclient.exe": "Rust",
    "deadbydaylight-win64-shipping.exe": "Dead by Daylight",
    "rainbowsix.exe": "Rainbow Six Siege",
    "rainbowsix_vulkan.exe": "Rainbow Six Siege",
    "destiny2.exe": "Destiny 2",
    "warframe.x64.exe": "Warframe",
    "pathofexile.exe": "Path of Exile",
    "pathofexile_x64.exe": "Path of Exile",
    "pathofexilesteam.exe": "Path of Exile",
    "pathofexile_x64steam.exe": "Path of Exile",
    "pathofexile2.exe": "Path of Exile 2",
    "pathofexile2_x64.exe": "Path of Exile 2",
    "pathofexile2steam.exe": "Path of Exile 2",
    "swgr.exe": "Star Wars: Galactic Racer",
    "swgr-win64-shipping.exe": "Star Wars: Galactic Racer",
    "dnfduel.exe": "DNF Duel",
    "dnfduel-win64-shipping.exe": "DNF Duel",
    "tekken8.exe": "Tekken 8",
    "tekken8-win64-shipping.exe": "Tekken 8",
    "sf6.exe": "Street Fighter 6",
    "mk12.exe": "Mortal Kombat 1",
    "pubg.exe": "PUBG: Battlegrounds",
    "tslgame.exe": "PUBG: Battlegrounds",
    "cod.exe": "Call of Duty",
    "warzone.exe": "Call of Duty: Warzone",
    "modernwarfare.exe": "Call of Duty: Modern Warfare",
    "blackops6.exe": "Call of Duty: Black Ops 6",
    "bo6.exe": "Call of Duty: Black Ops 6",
    "eurotrucks2.exe": "Euro Truck Simulator 2",
    "amtrucks.exe": "American Truck Simulator",
    "beamng.drive.x64.exe": "BeamNG.drive",
    "assettocorsa.exe": "Assetto Corsa",
    "acs.exe": "Assetto Corsa Competizione",
    "wutheringwaves.exe": "Wuthering Waves",
    "wutheringwaves-win64-shipping.exe": "Wuthering Waves",
    "terraria.exe": "Terraria",
    "hades.exe": "Hades",
    "hades2.exe": "Hades II",
    "hollow_knight.exe": "Hollow Knight",
    "stardew valley.exe": "Stardew Valley",
    "subnautica.exe": "Subnautica",
    "marvelrivals.exe": "Marvel Rivals"
}

# Standard non-game applications & background services to ignore
NON_GAME_APPS = {
    "explorer.exe", "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe",
    "code.exe", "devenv.exe", "pycharm64.exe", "idea64.exe", "notepad.exe", "notepad++.exe", "sublime_text.exe",
    "cmd.exe", "powershell.exe", "conhost.exe", "windows terminal.exe", "windowsterminal.exe",
    "python.exe", "pythonw.exe", "taskmgr.exe", "discord.exe", "spotify.exe", "whatsapp.exe", "telegram.exe",
    "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe", "riotclientservices.exe",
    "vlc.exe", "obs64.exe", "slack.exe", "teams.exe", "system idle process",
    # Antigravity IDE and AI tools (NEVER games)
    "antigravity ide.exe", "antigravity ide", "antigravity.exe", "agy.exe",
    "geminiapplauncher.exe", "geminicrashpadhandler.exe", "ollama.exe", "ollama app.exe",
    # Helper utilities & Anti-cheat services
    "epicwebhelper.exe", "crashreportclient.exe", "crashpad_handler.exe", "unins000.exe", "dxsetup.exe",
    "easyanticheat.exe", "easyanticheat_eos.exe", "beservice.exe", "beservice_x64.exe",
    "rockstarservice.exe", "rockstarsteamhelper.exe", "rockstar-games-launcher.exe", "socialclubhelper.exe",
    "unitycrashhandler64.exe", "unitycrashhandler32.exe", "riotclientcrashhandler.exe",
    "battlenet.exe", "agent.exe", "eaconnect_interface.exe", "ealauncher.exe"
}

# Substring keywords that strictly disqualify an application from being a game
BLACKLIST_KEYWORDS = [
    "antigravity", "gemini", "electron", "vscode", "pycharm", "visual studio",
    "terminal", "python", "taskmgr", "explorer", "browser", "whatsapp", "telegram"
]

# Gaming directory markers for autonomous detection of unknown games
GAME_DIR_MARKERS = [
    "/steamapps/common/",
    "/steamlibrary/",
    "/epic games/",
    "/games/",
    "/riot games/",
    "/gog galaxy/games/",
    "/gog games/",
    "/ubisoft/",
    "/ubisoft game launcher/games/",
    "/ea games/",
    "/blizzard/",
    "/battle.net/"
]

def is_blacklisted_app(name: str, full_path: str = "", win_title: str = "") -> bool:
    """Strictly checks if an application is an editor, IDE, browser, or desktop utility."""
    n_lower = (name or "").lower()
    p_lower = (full_path or "").lower().replace("\\", "/")
    t_lower = (win_title or "").lower()
    
    if n_lower in NON_GAME_APPS:
        return True
    if any(k in n_lower for k in BLACKLIST_KEYWORDS):
        return True
    if any(k in p_lower for k in ["/antigravity", "/gemini", "/pythonproject", "/microsoft vs code", "/google/chrome"]):
        return True
    if any(k in t_lower for k in ["antigravity ide", "visual studio code", "pycharm", "google chrome"]):
        return True
    return False

def identify_game(name: str, full_path: str = "", win_title: str = "", custom_games: Optional[List[str]] = None) -> Optional[str]:
    """
    Intelligently identifies if a process is a genuine game.
    Returns the clean display title, or None if it's not a game.
    """
    if is_blacklisted_app(name, full_path, win_title):
        return None
        
    n_lower = (name or "").lower()
    
    # 1. Known game dictionary
    if n_lower in KNOWN_GAME_EXES:
        return KNOWN_GAME_EXES[n_lower]
        
    # 2. User-configured custom games
    if custom_games and n_lower in custom_games:
        return win_title or name
        
    # 3. Game library directory check (e.g. Steam, Epic, E:\Games, D:\Games)
    dir_game = is_game_path(full_path)
    if dir_game:
        return win_title or dir_game
        
    # 4. Game engine executable suffix (Unreal / Unity shipping binaries)
    if n_lower.endswith("-shipping.exe") or n_lower.endswith("_shipping.exe"):
        clean = os.path.splitext(name)[0].replace("-Win64-Shipping", "").replace("_", " ").title()
        return win_title or clean
        
    return None

def is_same_game(session: 'GameSessionTracker', fg_name: str, fg_path: str, fg_game_title: str) -> bool:
    """Determines if the foreground process belongs to the same game session (e.g. launcher vs engine)."""
    if not session or not fg_name:
        return False
    if session.title.lower() == (fg_game_title or "").lower():
        return True
    # Folder match (e.g. E:\Games\STAR WARS - Galactic Racer)
    if session.exe_path and fg_path:
        s_dir = os.path.dirname(session.exe_path).lower().replace("\\", "/")
        f_dir = os.path.dirname(fg_path).lower().replace("\\", "/")
        if s_dir in f_dir or f_dir in s_dir:
            return True
    # Name prefix match (e.g. SWGR.exe vs SWGR-Win64-Shipping.exe)
    s_base = os.path.splitext(session.name)[0].lower()
    f_base = os.path.splitext(fg_name)[0].lower()
    if s_base in f_base or f_base in s_base:
        return True
    return False

# Process path and info cache (avoids repeated disk access & elevated query API calls)
_PID_INFO_CACHE: Dict[int, Any] = {}
_PID_CACHE_TTL = 30.0

def get_process_info(pid: int):
    """
    Safely retrieves (process_name, full_path) for any PID,
    handling elevated processes and anti-cheat hooks.
    Uses in-memory caching to eliminate redundant disk & API calls.
    """
    now = time.time()
    if pid in _PID_INFO_CACHE:
        c_name, c_path, c_time = _PID_INFO_CACHE[pid]
        if now - c_time < _PID_CACHE_TTL:
            return c_name, c_path

    proc_name = ""
    full_path = ""
    
    # 1. Try psutil
    try:
        p = psutil.Process(pid)
        proc_name = p.name()
        try:
            full_path = p.exe()
        except Exception:
            pass
    except Exception:
        pass
        
    # 2. Win32 QueryFullProcessImageNameW fallback for elevated / anti-cheat processes
    if not full_path or not proc_name:
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h_proc:
            try:
                buf = ctypes.create_unicode_buffer(1024)
                size = wintypes.DWORD(1024)
                if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                    full_path = buf.value
                    if not proc_name:
                        proc_name = os.path.basename(full_path)
            finally:
                kernel32.CloseHandle(h_proc)

    # Evict oldest if cache exceeds 300 entries
    if len(_PID_INFO_CACHE) > 300:
        oldest_pids = sorted(_PID_INFO_CACHE.keys(), key=lambda k: _PID_INFO_CACHE[k][2])[:50]
        for op in oldest_pids:
            _PID_INFO_CACHE.pop(op, None)
            
    _PID_INFO_CACHE[pid] = (proc_name, full_path, now)
    return proc_name, full_path

def is_game_path(full_path: str):
    """
    Checks if an executable path is inside any known gaming library/directory.
    Returns clean game title extracted from path if found.
    """
    if not full_path:
        return None
        
    norm_path = full_path.replace("\\", "/").lower()
    base_name = os.path.basename(full_path).lower()
    
    if (base_name in NON_GAME_APPS or base_name.startswith("unins") or 
        "crash" in base_name or "redist" in norm_path or "setup" in base_name or "installer" in base_name):
        return None
        
    for marker in GAME_DIR_MARKERS:
        if marker in norm_path:
            try:
                idx = norm_path.find(marker) + len(marker)
                rest = full_path[idx:].replace("\\", "/")
                folder = rest.split("/")[0]
                if folder and not folder.lower().endswith(".exe") and len(folder) > 2:
                    return folder
            except Exception:
                pass
            return os.path.splitext(base_name)[0].replace("-Win64-Shipping", "").replace("_", " ").title()
            
    return None

class GameSessionTracker:
    def __init__(self, pid: int, name: str, title: str, exe_path: str = ""):
        self.pid = pid
        self.name = name
        self.title = title
        self.exe_path = exe_path
        self.start_time = time.time()
        self.end_time = None
        
        self.samples = 0
        self.cpu_samples: List[float] = []
        self.gpu_samples: List[float] = []
        self.gpu_temp_samples: List[float] = []
        self.vram_samples: List[float] = []
        self.ram_samples: List[float] = []
        self.disk_read_samples: List[float] = []
        
        self.events: List[Dict[str, str]] = []
        self.add_event("SESSION_START", f"Launched {self.title} ({self.name})")

    def add_event(self, tag: str, message: str):
        t_str = time.strftime("%H:%M:%S")
        self.events.append({
            "time": t_str,
            "tag": tag,
            "message": message
        })

    def record_sample(self, telemetry: Dict[str, Any]):
        self.samples += 1
        cpu_val = telemetry["cpu"]["total"]
        gpu = telemetry["gpu"]
        gpu_val = gpu["utilization"] if gpu["available"] else 0.0
        gpu_temp = gpu["temperature"] if gpu["available"] else 0.0
        vram_val = (gpu["mem_used_mb"] / 1024.0) if gpu["available"] else 0.0
        ram_val = telemetry["memory"]["used_gb"]
        disk_read = telemetry["disk"]["read_mb_s"]
        
        self.cpu_samples.append(cpu_val)
        self.gpu_samples.append(gpu_val)
        self.gpu_temp_samples.append(gpu_temp)
        self.vram_samples.append(vram_val)
        self.ram_samples.append(ram_val)
        self.disk_read_samples.append(disk_read)
        
        # Check for anomalies during gameplay
        if gpu["available"] and gpu_temp >= 78:
            if not any(e["tag"] == "THERMAL_SPIKE" and (time.time() - self.start_time) < 30 for e in self.events[-3:]):
                self.add_event("THERMAL_SPIKE", f"GPU temp reached {gpu_temp}°C under load.")
        elif cpu_val >= 88:
            if not any(e["tag"] == "CPU_BOTTLENECK" for e in self.events[-3:]):
                self.add_event("CPU_BOTTLENECK", f"CPU load peaked at {cpu_val:.1f}%.")
        elif disk_read >= 45.0:
            if not any(e["tag"] == "ASSET_STREAM" for e in self.events[-3:]):
                self.add_event("ASSET_STREAM", f"Heavy asset streaming burst ({disk_read:.1f} MB/s read).")

    def finalize(self) -> Dict[str, Any]:
        self.end_time = time.time()
        duration_sec = max(1, int(self.end_time - self.start_time))
        mins = duration_sec // 60
        secs = duration_sec % 60
        duration_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"
        
        self.add_event("SESSION_END", f"Game process exited. Session duration: {duration_str}")
        
        avg_cpu = sum(self.cpu_samples) / max(1, len(self.cpu_samples))
        peak_cpu = max(self.cpu_samples) if self.cpu_samples else 0.0
        
        avg_gpu = sum(self.gpu_samples) / max(1, len(self.gpu_samples))
        peak_gpu = max(self.gpu_samples) if self.gpu_samples else 0.0
        
        avg_gpu_temp = sum(self.gpu_temp_samples) / max(1, len(self.gpu_temp_samples))
        peak_gpu_temp = max(self.gpu_temp_samples) if self.gpu_temp_samples else 0.0
        
        avg_vram = sum(self.vram_samples) / max(1, len(self.vram_samples))
        peak_vram = max(self.vram_samples) if self.vram_samples else 0.0
        
        avg_ram = sum(self.ram_samples) / max(1, len(self.ram_samples))
        peak_ram = max(self.ram_samples) if self.ram_samples else 0.0
        
        peak_disk = max(self.disk_read_samples) if self.disk_read_samples else 0.0
        
        grade = "S"
        verdict_notes = []
        if peak_gpu_temp >= 82:
            grade = "B"
            verdict_notes.append("GPU operated near thermal limit (82°C+). Ramp fans or check case airflow.")
        elif peak_gpu_temp >= 75:
            grade = "A"
            verdict_notes.append("GPU thermal load elevated but safe. Peak temperature stabilized.")
        else:
            verdict_notes.append("Thermal headroom optimal. RTX 3060 maintained cool operation.")
            
        if peak_cpu >= 88:
            if grade == "S":
                grade = "A"
            verdict_notes.append("CPU experienced transient spikes near saturation during intensive scenes.")
        else:
            verdict_notes.append("CPU load balanced smoothly across 20 cores.")
            
        if peak_vram >= 10.5:
            verdict_notes.append("VRAM allocated near 12GB limit; consider lowering textures if stuttering.")
        else:
            verdict_notes.append(f"VRAM allocation healthy (peaked at {peak_vram:.1f} GB of 12.0 GB).")

        return {
            "title": self.title,
            "exe": self.name,
            "duration_str": duration_str,
            "duration_sec": duration_sec,
            "start_str": time.strftime("%H:%M:%S", time.localtime(self.start_time)),
            "end_str": time.strftime("%H:%M:%S", time.localtime(self.end_time)),
            "samples_count": self.samples,
            "grade": grade,
            "cpu": {
                "avg": avg_cpu,
                "peak": peak_cpu,
                "history": self.cpu_samples[-40:]
            },
            "gpu": {
                "avg_load": avg_gpu,
                "peak_load": peak_gpu,
                "avg_temp": avg_gpu_temp,
                "peak_temp": peak_gpu_temp,
                "avg_vram": avg_vram,
                "peak_vram": peak_vram,
                "history": self.gpu_samples[-40:],
                "temp_history": self.gpu_temp_samples[-40:]
            },
            "ram": {
                "avg": avg_ram,
                "peak": peak_ram
            },
            "disk": {
                "peak_read_mb": peak_disk
            },
            "verdict": verdict_notes,
            "events": self.events
        }

class GameMonitor:
    def __init__(self, on_session_complete: Optional[Callable[[Dict[str, Any]], None]] = None, on_session_start: Optional[Callable[[str, str], None]] = None):
        self.on_session_complete = on_session_complete
        self.on_session_start = on_session_start
        self.active_session: Optional[GameSessionTracker] = None
        self.last_completed_report: Optional[Dict[str, Any]] = None
        self.custom_games: List[str] = []
        self._last_bg_scan_time = 0.0

    def set_custom_games(self, game_list: List[str]):
        self.custom_games = [g.lower() for g in game_list if g]

    def update(self, telemetry: Dict[str, Any]):
        """
        Fast, non-blocking check called on each telemetry cycle.
        Features intelligent foreground game prioritization & session switching.
        """
        # 1. Probe the current foreground window
        fg_pid = 0
        fg_name = ""
        fg_path = ""
        fg_title = ""
        fg_game_title = None

        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                p_id = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p_id))
                if p_id.value > 4:
                    fg_pid = p_id.value
                    fg_name, fg_path = get_process_info(fg_pid)
                    title_buf = ctypes.create_unicode_buffer(512)
                    user32.GetWindowTextW(hwnd, title_buf, 512)
                    fg_title = title_buf.value.strip()
                    fg_game_title = identify_game(fg_name, fg_path, fg_title, self.custom_games)
        except Exception:
            pass

        # 2. If the foreground window is a confirmed GAME
        if fg_game_title:
            if self.active_session is None:
                # Start new game session immediately!
                self._start_session(fg_pid, fg_name, fg_game_title, fg_path)
                self.active_session.record_sample(telemetry)
                return
            else:
                # A session is already active
                if self.active_session.pid == fg_pid:
                    # Same process: continue recording
                    self.active_session.record_sample(telemetry)
                    return
                elif is_same_game(self.active_session, fg_name, fg_path, fg_game_title):
                    # Child/partner process of the same game (e.g. Launcher -> Engine)
                    self.active_session.pid = fg_pid
                    self.active_session.name = fg_name
                    self.active_session.exe_path = fg_path
                    self.active_session.record_sample(telemetry)
                    return
                else:
                    # An entirely DIFFERENT game is now in foreground! Switch sessions!
                    old_report = self.active_session.finalize()
                    self.last_completed_report = old_report
                    if self.on_session_complete:
                        self.on_session_complete(old_report)
                    self._start_session(fg_pid, fg_name, fg_game_title, fg_path)
                    self.active_session.record_sample(telemetry)
                    return

        # 3. Foreground window is NOT a game (e.g. alt-tabbed to desktop, browser, Discord)
        if self.active_session is not None:
            # Check if active game process is still alive without unnecessary disk path resolution
            still_running = False
            try:
                if psutil.pid_exists(self.active_session.pid):
                    p = psutil.Process(self.active_session.pid)
                    if p.is_running() and p.name().lower() == self.active_session.name.lower():
                        still_running = True
            except Exception:
                still_running = False

            if still_running:
                # Game is still alive in background; continue sampling
                self.active_session.record_sample(telemetry)
                return
            else:
                # Game closed -> finalize debrief report!
                report = self.active_session.finalize()
                self.last_completed_report = report
                self.active_session = None
                if self.on_session_complete:
                    self.on_session_complete(report)
                return

        # 4. If no session is active, run fallback background process scan (throttled to every 5.0s)
        now_ts = time.time()
        if now_ts - self._last_bg_scan_time >= 5.0:
            self._last_bg_scan_time = now_ts
            self._detect_background_game_launch(telemetry)

    def _detect_background_game_launch(self, telemetry: Dict[str, Any]):
        """Fast process iteration fallback for games launched in background."""
        try:
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    name = (p.info.get('name') or '').lower()
                    pid = p.info.get('pid') or 0
                    if pid <= 4 or is_blacklisted_app(name):
                        continue
                    
                    # Known game check
                    if name in KNOWN_GAME_EXES:
                        self._start_session(pid, p.info['name'], KNOWN_GAME_EXES[name])
                        return
                        
                    # Custom game check
                    if self.custom_games and name in self.custom_games:
                        self._start_session(pid, p.info['name'], p.info['name'])
                        return

                    # Engine suffix check
                    if name.endswith("-shipping.exe") or name.endswith("_shipping.exe"):
                        title = os.path.splitext(p.info['name'])[0].replace("-Win64-Shipping", "").replace("_", " ").title()
                        self._start_session(pid, p.info['name'], title)
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

    def _start_session(self, pid: int, name: str, title: str, exe_path: str = ""):
        self.active_session = GameSessionTracker(pid, name, title, exe_path)
        if self.on_session_start:
            try:
                self.on_session_start(title, name)
            except Exception as e:
                print(f"Error in on_session_start callback: {e}")

    def start_manual_tracking(self, app_name: str = "", win_title: str = "") -> bool:
        """Allows manual tracking of the current active window or specified app."""
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                proc_name, full_path = get_process_info(pid.value)
                title_buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, title_buf, 512)
                title = win_title or title_buf.value or proc_name
                self._start_session(pid.value, proc_name, title, full_path)
                return True
        except Exception:
            pass
        return False

    def stop_manual_tracking(self) -> Optional[Dict[str, Any]]:
        """Manually finalizes active session and returns report."""
        if self.active_session:
            report = self.active_session.finalize()
            self.last_completed_report = report
            self.active_session = None
            if self.on_session_complete:
                self.on_session_complete(report)
            return report
        return None

    def simulate_sample_session(self) -> Dict[str, Any]:
        """Generates a realistic test game session report for Cyberpunk 2077."""
        tracker = GameSessionTracker(18240, "Cyberpunk2077.exe", "Cyberpunk 2077")
        tracker.start_time = time.time() - 2535
        
        import random
        for _ in range(40):
            mock_tel = {
                "cpu": {"total": random.uniform(22.0, 52.0)},
                "gpu": {
                    "available": True,
                    "utilization": random.uniform(84.0, 99.0),
                    "temperature": random.randint(61, 72),
                    "mem_used_mb": random.uniform(5400, 7200)
                },
                "memory": {"used_gb": random.uniform(14.5, 16.8)},
                "disk": {"read_mb_s": random.uniform(0.5, 78.0)}
            }
            tracker.record_sample(mock_tel)
            
        tracker.add_event("ASSET_LOAD", "Asset streaming burst (78.2 MB/s read on C:\\).")
        tracker.add_event("PEAK_VRAM", "Maximum VRAM allocation 7.2 GB (safe within 12GB limit).")
        report = tracker.finalize()
        self.last_completed_report = report
        return report
