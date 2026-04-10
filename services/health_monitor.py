"""
Health Monitor - Background thread that periodically checks project health.
"""
import threading
import time
from typing import Callable
from datetime import datetime

from .process_service import get_process_service
from .project_service import get_project_service


class HealthMonitor:
    """Background monitor for checking project health."""
    
    def __init__(self, interval: int = 5):
        """
        Initialize the health monitor.
        
        Args:
            interval: Check interval in seconds
        """
        self.interval = interval
        self._running = False
        self._thread = None
        self._callbacks: list[Callable] = []
        self._process_service = get_process_service()
        self._project_service = get_project_service()
    
    def add_callback(self, callback: Callable):
        """Add a callback to be called on health changes."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def start(self):
        """Start the health monitor thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("Health monitor started")
    
    def stop(self):
        """Stop the health monitor thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        print("Health monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_all_projects()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Health monitor error: {e}")
                time.sleep(self.interval)
    
    def _check_all_projects(self):
        """Check health of all tracked projects."""
        running_processes = self._process_service.get_all_running()
        
        for proc_info in running_processes:
            try:
                old_status = proc_info.status
                new_status = self._process_service.update_health_status(proc_info.project_id)
                
                # Update project status in storage if changed
                if new_status != old_status:
                    self._project_service.update_status(
                        proc_info.project_id,
                        new_status,
                        pid=proc_info.pid if new_status == "running" else None
                    )
                    
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(proc_info.project_id, old_status, new_status)
                        except Exception as e:
                            print(f"Callback error: {e}")
                
            except Exception as e:
                print(f"Error checking project {proc_info.project_id}: {e}")
    
    def check_project(self, project_id: str) -> str:
        """Check health of a specific project."""
        return self._process_service.check_health(project_id)[0]
    
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running and self._thread and self._thread.is_alive()


# Singleton instance
_health_monitor = None


def get_health_monitor(interval: int = 5) -> HealthMonitor:
    """Get the singleton health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor(interval=interval)
    return _health_monitor
