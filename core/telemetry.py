"""
Hardware & System Telemetry Engine
Monitors CPU (all cores), RAM, GPU (NVIDIA via nvidia-smi), Disks, Network, and Top Processes.
"""

import time
import os
import sys
import subprocess
import threading
import ctypes
from ctypes import byref, c_uint, c_ulonglong, Structure, create_string_buffer
from typing import Dict, List, Any, Optional
import psutil

# Structure definitions for direct in-memory NVML calls (0 subprocess overhead, 0 disk I/O)
class nvmlUtilization_t(Structure):
    _fields_ = [('gpu', c_uint), ('memory', c_uint)]

class nvmlMemory_t(Structure):
    _fields_ = [('total', c_ulonglong), ('free', c_ulonglong), ('used', c_ulonglong)]

class NVMLDirectDriver:
    """Provides instant in-process GPU metrics via nvml.dll without spawning subprocesses."""
    def __init__(self):
        self.available = False
        self.name = "N/A"
        self._nvml = None
        self._handle = None
        self._init_driver()

    def _init_driver(self):
        candidate_paths = [
            r"C:\Windows\System32\nvml.dll",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll"
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    self._nvml = ctypes.CDLL(path)
                    if self._nvml.nvmlInit_v2() == 0:
                        h = ctypes.c_void_p()
                        if self._nvml.nvmlDeviceGetHandleByIndex_v2(0, byref(h)) == 0:
                            self._handle = h
                            name_buf = create_string_buffer(96)
                            self._nvml.nvmlDeviceGetName(self._handle, name_buf, 96)
                            self.name = name_buf.value.decode("utf-8")
                            self.available = True
                            return
                except Exception:
                    pass

    def query(self) -> Optional[Dict[str, Any]]:
        if not self.available or not self._handle:
            return None
        try:
            util = nvmlUtilization_t()
            self._nvml.nvmlDeviceGetUtilizationRates(self._handle, byref(util))
            mem = nvmlMemory_t()
            self._nvml.nvmlDeviceGetMemoryInfo(self._handle, byref(mem))
            temp = c_uint()
            self._nvml.nvmlDeviceGetTemperature(self._handle, 0, byref(temp))
            return {
                "available": True,
                "name": self.name,
                "utilization": float(util.gpu),
                "mem_used_mb": float(mem.used / (1024**2)),
                "mem_total_mb": float(mem.total / (1024**2)),
                "temperature": int(temp.value)
            }
        except Exception:
            return None

class TelemetryEngine:
    def __init__(self):
        self._last_time = time.time()
        self._last_disk_io = None
        self._last_net_io = None
        
        # High-performance in-memory GPU probe
        self._nvml_driver = NVMLDirectDriver()
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
        self._last_gpu_subprocess_time = 0.0
        
        # Low-overhead cached metrics
        self._cached_disks = []
        self._last_disk_query_time = 0.0
        
        self._cached_procs_cpu = []
        self._cached_procs_mem = []
        self._cached_total_procs = 0
        self._cached_thread_count = 0
        self._last_proc_query_time = 0.0
        
        self._cached_connections = 0
        self._last_conn_query_time = 0.0
        
        # Prime psutil CPU counters
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        
        # Query GPU initially (prefer direct in-memory NVML: 0.07ms)
        if self._nvml_driver.available:
            init_gpu = self._nvml_driver.query()
            if init_gpu:
                self._gpu_data = init_gpu
        else:
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
        
        # Disks space (Cached for 60s to eliminate continuous disk/MFT wakeups & controller polling)
        if now - self._last_disk_query_time >= 60.0 or not self._cached_disks:
            new_disks = []
            try:
                for part in psutil.disk_partitions(all=False):
                    if not part.mountpoint:
                        continue
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        new_disks.append({
                            "device": part.device or part.mountpoint,
                            "mountpoint": part.mountpoint,
                            "total_gb": usage.total / (1024**3),
                            "used_gb": usage.used / (1024**3),
                            "free_gb": usage.free / (1024**3),
                            "percent": usage.percent
                        })
                    except (PermissionError, OSError):
                        pass
                if new_disks:
                    self._cached_disks = new_disks
            except Exception:
                pass
            self._last_disk_query_time = now
        disks = self._cached_disks

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
        
        # Network connections count (Cached for 5.0s to avoid full socket table sweeps every cycle)
        if now - self._last_conn_query_time >= 5.0:
            try:
                self._cached_connections = len(psutil.net_connections(kind="inet"))
            except Exception:
                pass
            self._last_conn_query_time = now
        conn_count = self._cached_connections
            
        # GPU Metrics (Direct in-memory NVML: 0.07ms, 0 disk I/O, 0 subprocesses)
        if self._nvml_driver.available:
            nvml_res = self._nvml_driver.query()
            if nvml_res:
                with self._gpu_lock:
                    self._gpu_data = nvml_res
        else:
            # Fallback to nvidia-smi throttled to once every 4 seconds
            if now - self._last_gpu_subprocess_time >= 4.0:
                self._last_gpu_subprocess_time = now
                self._query_gpu_async()

        with self._gpu_lock:
            gpu_snapshot = dict(self._gpu_data)
            
        # Top Processes (Throttled to once every 3.0s to reduce process memory/thread traversal overhead)
        if now - self._last_proc_query_time >= 3.0 or not self._cached_procs_cpu:
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

                self._cached_procs_cpu = top_cpu_procs
                self._cached_procs_mem = top_mem_procs
                self._cached_total_procs = total_procs
                self._cached_thread_count = total_threads
            except Exception:
                pass
            self._last_proc_query_time = now
        else:
            top_cpu_procs = self._cached_procs_cpu
            top_mem_procs = self._cached_procs_mem
            total_procs = self._cached_total_procs
            total_threads = self._cached_thread_count
            
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
