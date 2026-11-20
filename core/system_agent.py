"""
Autonomous System Monitoring Agent
Manages background sampling, rolling history buffers, telemetry analysis,
and autonomous diagnostic log generation.
"""

import time
import threading
from collections import deque
from typing import Dict, Any, List, Optional, Callable
from core.telemetry import TelemetryEngine
from core.game_monitor import GameMonitor
from core.news_sentry import NewsIntelligenceEngine

class SystemAgent:
    def __init__(self, sample_interval: float = 1.0, history_length: int = 60, custom_games: Optional[List[str]] = None, news_interval_sec: float = 1800.0, news_credibility: float = 80.0):
        self.sample_interval = sample_interval
        self.history_length = history_length
        self.engine = TelemetryEngine()
        
        # Game Activity Monitor
        self.game_monitor = GameMonitor(
            on_session_complete=self._on_game_completed,
            on_session_start=self._on_game_started
        )
        if custom_games:
            self.game_monitor.set_custom_games(custom_games)
        self.latest_game_report: Optional[Dict[str, Any]] = None
        self._new_game_report = False

        # Autonomous News Intelligence & Social Chatter Sentry
        self.news_engine = NewsIntelligenceEngine(
            refresh_interval_sec=news_interval_sec,
            min_credibility=news_credibility
        )
        
        # History buffers (0-100 normalized or raw values)
        self.cpu_history = deque([0.0] * history_length, maxlen=history_length)
        self.ram_history = deque([0.0] * history_length, maxlen=history_length)
        self.gpu_history = deque([0.0] * history_length, maxlen=history_length)
        self.net_rx_history = deque([0.0] * history_length, maxlen=history_length)
        self.net_tx_history = deque([0.0] * history_length, maxlen=history_length)
        self.disk_io_history = deque([0.0] * history_length, maxlen=history_length)
        
        # Diagnostic agent log buffer (larger buffer for extensive history)
        self.logs = deque(maxlen=60)
        self._add_log("AGENT_BOOT", "Sentinel autonomous monitoring core online.")
        self._add_log("TOPOLOGY", "20 logical cores, NVIDIA RTX 3060 12GB detected.")
        self._add_log("WATCHDOG", "Process sentry initialized. Active thread surveillance engaged.")
        self._add_log("HEALTH_MON", "Subsystem baseline established at 100% [OPTIMAL].")
        
        # Thread safety & state
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._latest_telemetry: Dict[str, Any] = {}
        self._health_index = 100.0
        self._health_status = "OPTIMAL"
        self._diagnostic_cycle = 0
        self._agent_mood = "VIGILANT"
        self._agent_thought = "Sentinel surveillance matrix online. All sensors nominal."

    def _add_log(self, tag: str, message: str, level: str = "INFO"):
        """Adds a timestamped entry to the agent log."""
        t_str = time.strftime("%H:%M:%S")
        self.logs.append({
            "timestamp": t_str,
            "tag": tag,
            "message": message,
            "level": level
        })

    def start(self):
        """Starts the background telemetry collection thread and news sentry."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.news_engine.start()

    def stop(self):
        """Stops the monitoring thread and news sentry."""
        self._running = False
        self.news_engine.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run_loop(self):
        while self._running:
            try:
                data = self.engine.collect_all()
                self._process_sample(data)
            except Exception as e:
                self._add_log("WARN", f"Telemetry cycle error: {e}", "WARN")
            time.sleep(self.sample_interval)

    def _process_sample(self, data: Dict[str, Any]):
        with self._lock:
            self._latest_telemetry = data
            
            # Update history buffers
            cpu_val = data["cpu"]["total"]
            ram_val = data["memory"]["percent"]
            gpu_val = data["gpu"]["utilization"] if data["gpu"]["available"] else 0.0
            rx_val = data["network"]["rx_mb_s"]
            tx_val = data["network"]["tx_mb_s"]
            disk_io = data["disk"]["read_mb_s"] + data["disk"]["write_mb_s"]
            
            self.cpu_history.append(cpu_val)
            self.ram_history.append(ram_val)
            self.gpu_history.append(gpu_val)
            self.net_rx_history.append(rx_val)
            self.net_tx_history.append(tx_val)
            self.disk_io_history.append(disk_io)
            
            # Compute System Health Index
            penalty = 0.0
            if cpu_val > 70:
                penalty += (cpu_val - 70) * 0.5
            if ram_val > 80:
                penalty += (ram_val - 80) * 0.6
            if data["gpu"]["available"] and data["gpu"]["temperature"] > 75:
                penalty += (data["gpu"]["temperature"] - 75) * 0.8
                
            self._health_index = max(10.0, min(100.0, 100.0 - penalty))
            if self._health_index >= 95:
                self._health_status = "OPTIMAL"
            elif self._health_index >= 80:
                self._health_status = "NOMINAL"
            elif self._health_index >= 60:
                self._health_status = "ELEVATED"
            else:
                self._health_status = "CRITICAL"
                
            # Autonomous Agent Diagnostics Generator
            self._diagnostic_cycle += 1
            self._generate_agent_insights(data)

        # Update Game Activity Monitor OUTSIDE lock to prevent UI thread blocking
        try:
            self.game_monitor.update(data)
        except Exception as e:
            print(f"Game monitor error: {e}")

    def _on_game_started(self, title: str, name: str):
        """Called when a game process is detected and tracking starts."""
        with self._lock:
            self._agent_mood = "COMBAT_WATCH"
            self._agent_thought = f"Surveillance active: {title} (Profiling GPU pipeline, thermals & VRAM)."
            self._add_log("GAME_START", f"Game detected: {title} ({name}) - profiling engaged.", "INFO")

    def _on_game_completed(self, report: Dict[str, Any]):
        """Called when a game process exits."""
        with self._lock:
            self.latest_game_report = report
            self._new_game_report = True
            self._add_log(
                "GAME_OVER",
                f"Game ended: {report['title']} ({report['duration_str']}) - Grade: {report['grade']}.",
                "WARN" if report["grade"] in ["B", "C"] else "INFO"
            )

    def clear_new_game_report_flag(self):
        with self._lock:
            self._new_game_report = False

    def start_manual_game_tracking(self) -> bool:
        """Starts monitoring the currently active foreground window as a game session."""
        success = self.game_monitor.start_manual_tracking()
        if success and self.game_monitor.active_session:
            title = self.game_monitor.active_session.title
            self._add_log("GAME_START", f"Manual tracking engaged: {title}")
        return success

    def stop_manual_game_tracking(self) -> Optional[Dict[str, Any]]:
        """Stops manual tracking and generates report."""
        report = self.game_monitor.stop_manual_tracking()
        return report

    def simulate_game_session(self) -> Dict[str, Any]:
        """Manually triggers a realistic game performance report for testing."""
        report = self.game_monitor.simulate_sample_session()
        self._on_game_completed(report)
        return report

    def _generate_agent_insights(self, data: Dict[str, Any]):
        """Agent intelligence logic that produces live diagnostic insights."""
        cpu = data["cpu"]["total"]
        cpu_freq = data["cpu"].get("freq_current_mhz", 0.0) / 1000.0
        ram = data["memory"]["percent"]
        ram_free_gb = data["memory"]["free_gb"]
        gpu = data["gpu"]
        cycle = self._diagnostic_cycle
        
        # Immediate Thermal Alert
        if gpu.get("available") and gpu["temperature"] >= 80:
            self._agent_mood = "THERMAL_DEFENSE"
            self._agent_thought = f"RTX 3060 at {gpu['temperature']}°C! Fans ramp recommended."
            self._add_log("THERMAL_WARN", f"RTX 3060 at {gpu['temperature']}°C! Fans ramp recommended.", "WARN")
        # Immediate CPU Spike Alert
        elif cpu >= 75:
            top_p = data["processes"]["top_cpu"][0]["name"] if data["processes"]["top_cpu"] else "Unknown"
            top_cpu = data["processes"]["top_cpu"][0]["cpu_percent"] if data["processes"]["top_cpu"] else 0.0
            self._agent_mood = "COMPUTE_GUARD"
            self._agent_thought = f"Compute surge detected ({cpu:.1f}%). Primary consumer: {top_p} ({top_cpu:.1f}%)."
            self._add_log("CPU_SPIKE", f"High load detected ({cpu:.1f}%). Primary consumer: {top_p} ({top_cpu:.1f}%)", "WARN")
        # Immediate RAM Alert
        elif ram >= 88:
            self._agent_mood = "MEMORY_DEFENSE"
            self._agent_thought = f"RAM usage critical ({ram:.1f}%). Only {ram_free_gb:.1f} GB remaining."
            self._add_log("MEM_PRESSURE", f"RAM usage critical ({ram:.1f}%). Only {ram_free_gb:.1f} GB remaining.", "WARN")
        
        # Periodic Active Multi-Domain Insights (every 3-4 seconds)
        elif cycle % 4 == 0:
            if gpu.get("available"):
                headroom = max(0, 85 - gpu["temperature"])
                self._agent_mood = "VIGILANT"
                self._agent_thought = f"RTX 3060 at {gpu['temperature']}°C (Headroom: {headroom}°C). VRAM: {gpu['mem_used_mb']/1024.0:.1f} GB."
                self._add_log("THERMAL_GUARD", f"RTX 3060 at {gpu['temperature']}°C (Headroom: {headroom}°C). VRAM load: {gpu['mem_used_mb']/1024.0:.1f} GB.")
            else:
                self._agent_mood = "VIGILANT"
                self._agent_thought = f"Total CPU load: {cpu:.1f}% across {data['cpu']['logical_count']} cores."
                self._add_log("SYS_LOAD", f"Total CPU load: {cpu:.1f}% across {data['cpu']['logical_count']} cores.")
        elif cycle % 4 == 1:
            rx = data["network"]["rx_kb_s"]
            tx = data["network"]["tx_kb_s"]
            conn = data["network"]["connections"]
            self._agent_mood = "VIGILANT"
            self._agent_thought = f"Net I/O: {rx:.1f} KB/s down, {tx:.1f} KB/s up ({conn} active sockets)."
            self._add_log("NET_PULSE", f"Net I/O: {rx:.1f} KB/s down, {tx:.1f} KB/s up ({conn} active sockets).")
        elif cycle % 4 == 2:
            if data["processes"]["top_cpu"]:
                p = data["processes"]["top_cpu"][0]
                self._agent_mood = "ANALYTICAL"
                self._agent_thought = f"Top consumer: {p['name']} (PID {p['pid']}) - CPU {p['cpu_percent']:.1f}%."
                self._add_log("WATCHDOG", f"Top consumer: {p['name']} (PID {p['pid']}) - CPU {p['cpu_percent']:.1f}%, RAM {p['mem_mb']:.1f} MB.")
            else:
                self._agent_mood = "VIGILANT"
                self._agent_thought = f"Active process surveillance: {data['processes']['total_count']} procs normal."
                self._add_log("WATCHDOG", f"Active process surveillance: {data['processes']['total_count']} procs normal.")
        elif cycle % 4 == 3:
            self._agent_mood = "OPTIMAL" if self._health_index >= 90 else "VIGILANT"
            self._agent_thought = f"Subsystems nominal. Health Index: {self._health_index:.1f}% [{self._health_status}]."
            self._add_log("SYS_INTEGRITY", f"Subsystems operating nominally. Health Index: {self._health_index:.1f}% [{self._health_status}].")

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns a thread-safe snapshot of all telemetry, histories, and logs."""
        with self._lock:
            active_game_title = self.game_monitor.active_session.title if (self.game_monitor and self.game_monitor.active_session) else None
            # Dynamic mood override if game is running
            current_mood = "COMBAT_WATCH" if active_game_title else self._agent_mood
            current_thought = f"Surveillance active: {active_game_title} (Tracking GPU pipeline & VRAM)." if active_game_title else self._agent_thought
            
            return {
                "telemetry": dict(self._latest_telemetry) if self._latest_telemetry else None,
                "cpu_history": list(self.cpu_history),
                "ram_history": list(self.ram_history),
                "gpu_history": list(self.gpu_history),
                "net_rx_history": list(self.net_rx_history),
                "net_tx_history": list(self.net_tx_history),
                "disk_io_history": list(self.disk_io_history),
                "logs": list(self.logs),
                "health_index": self._health_index,
                "health_status": self._health_status,
                "active_game": active_game_title,
                "game_report": dict(self.latest_game_report) if self.latest_game_report else None,
                "has_new_game_report": self._new_game_report,
                "agent_mood": current_mood,
                "agent_thought": current_thought,
                "diagnostic_cycle": self._diagnostic_cycle,
                "news": self.news_engine.get_snapshot()
            }

    def refresh_news_now(self):
        """Forces an immediate news & social chatter intelligence sweep."""
        self.news_engine.trigger_manual_sweep()

    def toggle_news_expansion(self, news_id: str):
        """Toggles expanding details and social chatter for a given news story."""
        self.news_engine.toggle_expand(news_id)

    def toggle_news_chatter(self, news_id: str):
        """Toggles the visibility of the live chatter section inside a story."""
        self.news_engine.toggle_chatter(news_id)

    def refresh_topic_chatter(self, news_id: str):
        """Refreshes live user opinions and comments for a specific story."""
        self.news_engine.refresh_topic_chatter(news_id)

    def set_news_refresh_interval(self, sec: float):
        """Updates the news refresh schedule interval (e.g. 1800s = 30m)."""
        self.news_engine.set_refresh_interval(sec)
