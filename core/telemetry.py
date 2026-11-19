"""
Hardware & System Telemetry Engine
Monitors CPU (all cores), RAM, GPU (NVIDIA via nvidia-smi), Disks, Network, and Top Processes.
"""

import time
import os
import sys
import subprocess
import threading
from typing import Dict, List, Any, Optional
import psutil

class TelemetryEngine:
    def __init__(self):
        self._last_time = time.time()
        self._last_disk_io = None
        self._last_net_io = None
        
        # GPU telemetry cache and lock
        self._gpu_data = {
            "available": False,
            "name": "N/A",
            "utilization": 0,
            "mem_used_mb": 0,
            "mem_total_mb": 0,
            "temperature": 0
        }
        self._gpu_lock = threading.Lock()
        self._gpu_query_running = False
        
        # Prime psutil CPU counters
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        
        # Query GPU initially
        self._query_gpu_async()

    def _query_gpu_async(self):
        """Runs nvidia-smi in a background thread to avoid blocking telemetry."""
        if self._gpu_query_running:
            return

        def _worker():
            self._gpu_query_running = True
            try:
                # nvidia-smi query
                flags = 0
                if sys.platform == "win32":
                    flags = subprocess.CREATE_NO_WINDOW  # Do not open console window
                    
                res = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                        "--format=csv,noheader,nounits"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1.5,
                    creationflags=flags
                )
                if res.returncode == 0 and res.stdout.strip():
                    parts = [p.strip() for p in res.stdout.strip().split(",")]
                    if len(parts) >= 5:
                        with self._gpu_lock:
                            self._gpu_data = {
                                "available": True,
                                "name": parts[0],
                                "utilization": float(parts[1]) if parts[1].replace(".", "", 1).isdigit() else 0.0,
                                "mem_used_mb": float(parts[2]) if parts[2].replace(".", "", 1).isdigit() else 0.0,
                                "mem_total_mb": float(parts[3]) if parts[3].replace(".", "", 1).isdigit() else 0.0,
                                "temperature": int(float(parts[4])) if parts[4].replace(".", "", 1).isdigit() else 0
                            }
            except Exception:
                # nvidia-smi not available or timed out
                pass
            finally:
                self._gpu_query_running = False

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def collect_all(self) -> Dict[str, Any]:
        """Collects an instantaneous snapshot of system telemetry."""
        now = time.time()
        dt = max(now - self._last_time, 0.1)
        self._last_time = now
        
        # CPU Metrics
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True)
        cpu_count_logical = psutil.cpu_count(logical=True) or 1
        cpu_count_physical = psutil.cpu_count(logical=False) or 1
        
        freq = psutil.cpu_freq()
        cpu_freq_curr = freq.current if freq else 0.0
        cpu_freq_max = freq.max if freq else 0.0
        
        # RAM & Swap Metrics
        try:
            vm = psutil.virtual_memory()
            mem_data = {
                "total_gb": vm.total / (1024**3),
                "used_gb": vm.used / (1024**3),
                "free_gb": vm.available / (1024**3),
                "percent": vm.percent,
            }
        except Exception:
            mem_data = {
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "percent": 0.0,
            }

        try:
            swap = psutil.swap_memory()
            mem_data["swap_total_gb"] = swap.total / (1024**3)
            mem_data["swap_used_gb"] = swap.used / (1024**3)
            mem_data["swap_percent"] = swap.percent
        except Exception:
            mem_data["swap_total_gb"] = 0.0
            mem_data["swap_used_gb"] = 0.0
            mem_data["swap_percent"] = 0.0
        
        # Disk I/O delta
        current_disk_io = psutil.disk_io_counters()
        disk_read_bps = 0.0
        disk_write_bps = 0.0
        if current_disk_io and self._last_disk_io:
            read_delta = current_disk_io.read_bytes - self._last_disk_io.read_bytes
            write_delta = current_disk_io.write_bytes - self._last_disk_io.write_bytes
            disk_read_bps = max(0.0, read_delta / dt)
            disk_write_bps = max(0.0, write_delta / dt)
        self._last_disk_io = current_disk_io
        
        # Disks space
        disks = []
        try:
            for part in psutil.disk_partitions(all=False):
                if not part.mountpoint:
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        "device": part.device or part.mountpoint,
                        "mountpoint": part.mountpoint,
                        "total_gb": usage.total / (1024**3),
                        "used_gb": usage.used / (1024**3),
                        "free_gb": usage.free / (1024**3),
                        "percent": usage.percent
                    })
                except (PermissionError, OSError):
                    pass
        except Exception:
            pass

        # Network I/O delta
        current_net_io = psutil.net_io_counters()
        net_rx_bps = 0.0
        net_tx_bps = 0.0
        if current_net_io and self._last_net_io:
            rx_delta = current_net_io.bytes_recv - self._last_net_io.bytes_recv
            tx_delta = current_net_io.bytes_sent - self._last_net_io.bytes_sent
            net_rx_bps = max(0.0, rx_delta / dt)
            net_tx_bps = max(0.0, tx_delta / dt)
        self._last_net_io = current_net_io
        
        # Network connections count
        conn_count = 0
        try:
            conn_count = len(psutil.net_connections(kind="inet"))
        except Exception:
            pass
            
        # Trigger next GPU sample in background
        self._query_gpu_async()
        with self._gpu_lock:
            gpu_snapshot = dict(self._gpu_data)
            
        # Top Processes
        top_cpu_procs = []
        top_mem_procs = []
        total_procs = 0
        total_threads = 0
        
        try:
            all_procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'num_threads']):
                try:
                    info = p.info
                    total_procs += 1
                    total_threads += (info.get('num_threads') or 1)
                    all_procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Filter out System Idle Process (PID 0)
            real_procs = [p for p in all_procs if (p.get('pid') or 0) > 0 and 'idle' not in (p.get('name') or '').lower()]

            # Sort top CPU
            real_procs.sort(key=lambda x: (x.get('cpu_percent') or 0.0), reverse=True)
            for p in real_procs[:5]:
                mem_mb = (p['memory_info'].rss / (1024 * 1024)) if p.get('memory_info') else 0.0
                raw_cpu = p.get('cpu_percent') or 0.0
                norm_cpu = min(100.0, raw_cpu / max(1, cpu_count_logical))
                top_cpu_procs.append({
                    "pid": p.get('pid', 0),
                    "name": p.get('name', 'Unknown') or 'Unknown',
                    "cpu_percent": norm_cpu,
                    "mem_mb": mem_mb
                })
                
            # Sort top Memory
            real_procs.sort(key=lambda x: (x.get('memory_percent') or 0.0), reverse=True)
            for p in real_procs[:5]:
                mem_mb = (p['memory_info'].rss / (1024 * 1024)) if p.get('memory_info') else 0.0
                top_mem_procs.append({
                    "pid": p.get('pid', 0),
                    "name": p.get('name', 'Unknown') or 'Unknown',
                    "mem_percent": p.get('memory_percent') or 0.0,
                    "mem_mb": mem_mb
                })
        except Exception:
            pass
            
        # Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = int(now - boot_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        mins = (uptime_seconds % 3600) // 60
        secs = uptime_seconds % 60
        uptime_str = f"{days}d {hours:02d}h {mins:02d}m {secs:02d}s" if days > 0 else f"{hours:02d}h {mins:02d}m {secs:02d}s"

        # Battery (if available)
        battery_data = None
        try:
            b = psutil.sensors_battery()
            if b is not None:
                battery_data = {
                    "percent": b.percent,
                    "power_plugged": b.power_plugged,
                    "secsleft": b.secsleft
                }
        except Exception:
            pass

        return {
            "timestamp": now,
            "cpu": {
                "total": cpu_total,
                "cores": cpu_cores,
                "logical_count": cpu_count_logical,
                "physical_count": cpu_count_physical,
                "freq_current_mhz": cpu_freq_curr,
                "freq_max_mhz": cpu_freq_max
            },
            "memory": mem_data,
            "gpu": gpu_snapshot,
            "disk": {
                "read_mb_s": disk_read_bps / (1024 * 1024),
                "write_mb_s": disk_write_bps / (1024 * 1024),
                "partitions": disks
            },
            "network": {
                "rx_kb_s": net_rx_bps / 1024.0,
                "tx_kb_s": net_tx_bps / 1024.0,
                "rx_mb_s": (net_rx_bps / 1024.0) / 1024.0,
                "tx_mb_s": (net_tx_bps / 1024.0) / 1024.0,
                "connections": conn_count
            },
            "processes": {
                "top_cpu": top_cpu_procs,
                "top_memory": top_mem_procs,
                "total_count": total_procs,
                "thread_count": total_threads
            },
            "system": {
                "uptime": uptime_str,
                "uptime_seconds": uptime_seconds,
                "hostname": os.environ.get("COMPUTERNAME", "PC"),
                "battery": battery_data
            }
        }
