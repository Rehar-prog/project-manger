"""
System Service - Provides system monitoring metrics like CPU, RAM, disk usage.
"""
import time
import platform
from datetime import datetime, timedelta
from typing import Dict, Any
from dataclasses import dataclass, asdict

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class SystemMetrics:
    """System metrics data."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    uptime_seconds: int = 0
    platform: str = ""
    timestamp: str = ""


class SystemService:
    """Service for monitoring system resources."""
    
    def __init__(self):
        self._start_time = datetime.now()
        self._cache = {}
        self._cache_time = 0
        self._cache_ttl = 2  # Cache for 2 seconds
    
    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        metrics = SystemMetrics()
        metrics.platform = platform.platform()
        metrics.timestamp = datetime.now().isoformat()
        
        if PSUTIL_AVAILABLE:
            # CPU
            metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory
            mem = psutil.virtual_memory()
            metrics.memory_percent = mem.percent
            metrics.memory_used_gb = round(mem.used / (1024**3), 2)
            metrics.memory_total_gb = round(mem.total / (1024**3), 2)
            
            # Disk
            disk = psutil.disk_usage('/')
            metrics.disk_percent = disk.percent
            metrics.disk_used_gb = round(disk.used / (1024**3), 2)
            metrics.disk_total_gb = round(disk.total / (1024**3), 2)
        else:
            # Fallback values when psutil is not available
            metrics.cpu_percent = 0.0
            metrics.memory_percent = 0.0
            metrics.disk_percent = 0.0
        
        # Uptime
        uptime = datetime.now() - self._start_time
        metrics.uptime_seconds = int(uptime.total_seconds())
        
        return metrics
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary."""
        metrics = self.get_metrics()
        return {
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_used_gb": metrics.memory_used_gb,
            "memory_total_gb": metrics.memory_total_gb,
            "disk_percent": metrics.disk_percent,
            "disk_used_gb": metrics.disk_used_gb,
            "disk_total_gb": metrics.disk_total_gb,
            "uptime_seconds": metrics.uptime_seconds,
            "uptime_formatted": self._format_uptime(metrics.uptime_seconds),
            "platform": metrics.platform,
            "timestamp": metrics.timestamp
        }
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human-readable format."""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_cached_metrics(self) -> Dict[str, Any]:
        """Get cached metrics, refresh if cache expired."""
        current_time = time.time()
        if current_time - self._cache_time > self._cache_ttl or not self._cache:
            self._cache = self.get_metrics_dict()
            self._cache_time = current_time
        return self._cache
    
    def get_process_info(self, pid: int) -> Dict[str, Any]:
        """Get information about a specific process."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}
        
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return {
                    "pid": pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_percent": proc.memory_percent(),
                    "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
                    "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                    "running": proc.is_running()
                }
        except psutil.NoSuchProcess:
            return {"error": "Process not found", "pid": pid}
        except Exception as e:
            return {"error": str(e), "pid": pid}
    
    def get_all_processes(self) -> Dict[str, Any]:
        """Get information about all running processes."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available", "processes": []}
        
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    pinfo['memory_mb'] = round(proc.memory_info().rss / (1024 * 1024), 2)
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            return {
                "total_processes": len(processes),
                "processes": processes[:50]  # Return top 50 by memory
            }
        except Exception as e:
            return {"error": str(e), "processes": []}


# Singleton instance
_system_service = None


def get_system_service() -> SystemService:
    """Get the singleton system service instance."""
    global _system_service
    if _system_service is None:
        _system_service = SystemService()
    return _system_service
