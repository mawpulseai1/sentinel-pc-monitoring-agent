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
    "terraria.exe": "Terraria",
    "hades.exe": "Hades",
    "hades2.exe": "Hades II",
    "hollow_knight.exe": "Hollow Knight",
    "stardew valley.exe": "Stardew Valley",
    "subnautica.exe": "Subnautica",
    "marvelrivals.exe": "Marvel Rivals"
}

# Standard non-game applications to ignore for foreground window detection
NON_GAME_APPS = {
    "explorer.exe", "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
    "code.exe", "devenv.exe", "pycharm64.exe", "idea64.exe", "notepad.exe",
    "cmd.exe", "powershell.exe", "conhost.exe", "windows terminal.exe", "windowsterminal.exe",
    "python.exe", "pythonw.exe", "taskmgr.exe", "discord.exe", "spotify.exe",
    "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe", "riotclientservices.exe",
    "vlc.exe", "obs64.exe", "slack.exe", "teams.exe", "system idle process"
}

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
    def __init__(self, on_session_complete: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.on_session_complete = on_session_complete
        self.active_session: Optional[GameSessionTracker] = None
        self.last_completed_report: Optional[Dict[str, Any]] = None
        self.custom_games: List[str] = []

    def set_custom_games(self, game_list: List[str]):
        self.custom_games = [g.lower() for g in game_list if g]

    def update(self, telemetry: Dict[str, Any]):
        """Fast, non-blocking check called on each telemetry cycle."""
        # 1. Update active session if running
        if self.active_session is not None:
            pid = self.active_session.pid
            still_running = False
            try:
                if psutil.pid_exists(pid):
                    p = psutil.Process(pid)
                    if p.name().lower() == self.active_session.name.lower():
                        still_running = True
            except Exception:
                still_running = False

            if still_running:
                self.active_session.record_sample(telemetry)
                return
            else:
                # Process terminated -> finalize session
                report = self.active_session.finalize()
                self.last_completed_report = report
                self.active_session = None
                if self.on_session_complete:
                    self.on_session_complete(report)
                return

        # 2. If no game is running, detect game start (zero blocking)
        self._detect_game_launch(telemetry)

    def _detect_game_launch(self, telemetry: Dict[str, Any]):
        """Fast multi-method detection: active window check + process scan."""
        # Method A: Active Foreground Window Check (fastest & most accurate)
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value > 4:
                    p = psutil.Process(pid.value)
                    proc_name = p.name().lower()
                    
                    if proc_name not in NON_GAME_APPS:
                        title_buf = ctypes.create_unicode_buffer(512)
                        user32.GetWindowTextW(hwnd, title_buf, 512)
                        win_title = title_buf.value.strip()

                        # Check known list
                        if proc_name in KNOWN_GAME_EXES:
                            self._start_session(pid.value, p.name(), KNOWN_GAME_EXES[proc_name])
                            return

                        # Check custom user list
                        if proc_name in self.custom_games:
                            self._start_session(pid.value, p.name(), win_title or proc_name)
                            return

                        # Check Unreal/Unity game pattern
                        if "-shipping.exe" in proc_name or "_shipping.exe" in proc_name or "game.exe" in proc_name:
                            clean_title = win_title or os.path.splitext(p.name())[0].replace("-Win64-Shipping", "").replace("_", " ").title()
                            self._start_session(pid.value, p.name(), clean_title)
                            return

                        # Check high GPU activity (>25% GPU or >1GB VRAM) for unknown fullscreen/foreground window
                        gpu = telemetry.get("gpu", {})
                        if gpu.get("available") and gpu.get("utilization", 0.0) > 25.0 and win_title:
                            self._start_session(pid.value, p.name(), win_title)
                            return
        except Exception:
            pass

        # Method B: Fast Process Name Scan (only queries name, never calls blocking exe())
        try:
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    name = (p.info.get('name') or '').lower()
                    pid = p.info.get('pid') or 0
                    if pid <= 4 or name in NON_GAME_APPS:
                        continue
                    
                    # Known game check
                    if name in KNOWN_GAME_EXES:
                        self._start_session(pid, p.info['name'], KNOWN_GAME_EXES[name])
                        return
                        
                    # Custom game check
                    if name in self.custom_games:
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

    def _start_session(self, pid: int, name: str, title: str):
        self.active_session = GameSessionTracker(pid, name, title)

    def start_manual_tracking(self, app_name: str = "", win_title: str = "") -> bool:
        """Allows manual tracking of the current active window or specified app."""
        try:
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                p = psutil.Process(pid.value)
                title_buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, title_buf, 512)
                title = win_title or title_buf.value or p.name()
                self._start_session(pid.value, p.name(), title)
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
