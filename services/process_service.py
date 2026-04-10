"""
Process Service - Manages process lifecycle, starting, stopping, and monitoring.
Uses psutil for robust process management on Windows.
Supports multi-service projects.
"""
import subprocess
import os
import signal
import time
import threading
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Process management will be limited.")


@dataclass
class ServiceProcessInfo:
    """Runtime information about a running service process."""
    project_id: str
    service_id: str
    process: subprocess.Popen = None
    pid: int = None
    started_at: str = ""
    stopped_at: str = ""
    status: str = "stopped"  # running, stopped, crashed
    exit_code: int = None
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "service_id": self.service_id,
            "pid": self.pid,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "status": self.status,
            "exit_code": self.exit_code,
            "error_message": self.error_message
        }


@dataclass 
class ProcessInfo:
    """Legacy ProcessInfo for backward compatibility."""
    project_id: str
    process: subprocess.Popen = None
    pid: int = None
    started_at: str = ""
    stopped_at: str = ""
    status: str = "stopped"
    exit_code: int = None
    error_message: str = ""


class ProcessService:
    """Service for managing process lifecycle with multi-service support."""
    
    def __init__(self):
        # Key format: "project_id:service_id"
        self._processes: Dict[str, ServiceProcessInfo] = {}
        self._lock = threading.Lock()
    
    def _get_key(self, project_id: str, service_id: str) -> str:
        """Get storage key for a service."""
        return f"{project_id}:{service_id}"
    
    def start_service(self, project_id: str, service_id: str, 
                      directory: str, start_cmd: str) -> tuple[bool, str, Optional[ServiceProcessInfo]]:
        """Start a specific service.
        
        Args:
            project_id: The project ID
            service_id: The service ID
            directory: Working directory
            start_cmd: Command to run
            
        Returns:
            (success, message, process_info)
        """
        key = self._get_key(project_id, service_id)
        
        with self._lock:
            # Check if already running
            if key in self._processes:
                existing = self._processes[key]
                if existing.status == "running":
                    # Verify process is actually alive
                    if self._is_process_alive(existing.pid):
                        return False, "Service is already running", existing
                    else:
                        # Process died, clean it up
                        del self._processes[key]
            
            try:
                # Validate directory
                if not os.path.exists(directory):
                    return False, f"Directory does not exist: {directory}", None
                
                # Start the process
                process_kwargs = {
                    'cwd': directory,
                    'shell': True,
                    'stdout': subprocess.DEVNULL,
                    'stderr': subprocess.DEVNULL,
                    'stdin': subprocess.DEVNULL,
                }
                
                if os.name == 'nt':
                    # Windows: Create new process group for proper signal handling
                    process_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    # Linux/Mac: Start in new session for proper signal handling
                    process_kwargs['start_new_session'] = True
                
                process = subprocess.Popen(start_cmd, **process_kwargs)
                
                # Small delay to check if process started successfully
                time.sleep(0.5)
                
                if process.poll() is not None and process.poll() != 0:
                    return False, f"Process exited immediately with code {process.poll()}", None
                
                # Create process info
                proc_info = ServiceProcessInfo(
                    project_id=project_id,
                    service_id=service_id,
                    process=process,
                    pid=process.pid,
                    started_at=datetime.now().isoformat(),
                    status="running"
                )
                
                self._processes[key] = proc_info
                
                return True, "Service started successfully", proc_info
                
            except Exception as e:
                return False, f"Failed to start process: {str(e)}", None
    
    def stop_service(self, project_id: str, service_id: str, 
                     stop_cmd: str = None, directory: str = None) -> tuple[bool, str]:
        """Stop a specific service.
        
        Args:
            project_id: The project ID
            service_id: The service ID
            stop_cmd: Optional custom stop command
            directory: Working directory for stop command
            
        Returns:
            (success, message)
        """
        key = self._get_key(project_id, service_id)
        
        with self._lock:
            proc_info = self._processes.get(key)
            if not proc_info:
                return False, "Service is not running"
            
            if proc_info.status != "running":
                return False, "Service is not in running state"
            
            success = False
            message = ""
            
            try:
                # Step 1: Try custom stop command if provided
                if stop_cmd and directory and os.path.exists(directory):
                    try:
                        subprocess.run(
                            stop_cmd,
                            cwd=directory,
                            shell=True,
                            timeout=5,
                            capture_output=True
                        )
                        time.sleep(1)
                    except Exception as e:
                        print(f"Custom stop command failed: {e}")
                
                # Step 2: Try graceful termination
                if PSUTIL_AVAILABLE and proc_info.pid:
                    success = self._terminate_process_tree(proc_info.pid)
                else:
                    # Fallback to basic terminate
                    if proc_info.process:
                        proc_info.process.terminate()
                        try:
                            proc_info.process.wait(timeout=5)
                            success = True
                        except subprocess.TimeoutExpired:
                            pass
                
                # Step 3: Force kill if graceful failed
                if not success and proc_info.process:
                    try:
                        if os.name == 'nt':
                            # Windows: Use standard kill
                            proc_info.process.kill()
                            proc_info.process.wait(timeout=2)
                        else:
                            # Linux/Mac: Kill entire process group
                            pgid = os.getpgid(proc_info.process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                            proc_info.process.wait(timeout=2)
                        success = True
                    except Exception:
                        pass
                
                # Update process info
                proc_info.stopped_at = datetime.now().isoformat()
                proc_info.status = "stopped"
                proc_info.process = None
                
                # Remove from tracking
                if key in self._processes:
                    del self._processes[key]
                
                if success:
                    message = "Service stopped successfully"
                else:
                    message = "Service may still be running (could not verify termination)"
                
                return success, message
                
            except Exception as e:
                proc_info.stopped_at = datetime.now().isoformat()
                proc_info.status = "stopped"
                proc_info.process = None
                if key in self._processes:
                    del self._processes[key]
                return False, f"Error stopping service: {str(e)}"
    
    def restart_service(self, project_id: str, service_id: str,
                        directory: str, start_cmd: str, 
                        stop_cmd: str = None) -> tuple[bool, str, Optional[ServiceProcessInfo]]:
        """Restart a specific service."""
        self.stop_service(project_id, service_id, stop_cmd, directory)
        time.sleep(0.5)
        return self.start_service(project_id, service_id, directory, start_cmd)
    
    # Legacy methods for backward compatibility (single service projects)
    def start_project(self, project_id: str, directory: str, 
                      start_cmd: str) -> tuple[bool, str, Optional[ProcessInfo]]:
        """Start the default service of a project (backward compatibility)."""
        success, message, info = self.start_service(project_id, "default", directory, start_cmd)
        
        if success and info:
            # Return legacy ProcessInfo format
            legacy_info = ProcessInfo(
                project_id=project_id,
                process=info.process,
                pid=info.pid,
                started_at=info.started_at,
                status=info.status
            )
            return success, message, legacy_info
        return success, message, None
    
    def stop_project(self, project_id: str, stop_cmd: str = None,
                     directory: str = None) -> tuple[bool, str]:
        """Stop the default service of a project (backward compatibility)."""
        return self.stop_service(project_id, "default", stop_cmd, directory)
    
    def restart_project(self, project_id: str, directory: str, 
                        start_cmd: str, stop_cmd: str = None) -> tuple[bool, str, Optional[ProcessInfo]]:
        """Restart the default service of a project (backward compatibility)."""
        success, message, info = self.restart_service(project_id, "default", directory, start_cmd, stop_cmd)
        
        if success and info:
            legacy_info = ProcessInfo(
                project_id=project_id,
                process=info.process,
                pid=info.pid,
                started_at=info.started_at,
                status=info.status
            )
            return success, message, legacy_info
        return success, message, None
    
    def get_service_info(self, project_id: str, service_id: str) -> Optional[ServiceProcessInfo]:
        """Get process info for a specific service."""
        key = self._get_key(project_id, service_id)
        return self._processes.get(key)
    
    def get_process_info(self, project_id: str) -> Optional[ProcessInfo]:
        """Get process info for default service (backward compatibility)."""
        info = self.get_service_info(project_id, "default")
        if info:
            return ProcessInfo(
                project_id=project_id,
                process=info.process,
                pid=info.pid,
                started_at=info.started_at,
                status=info.status
            )
        return None
    
    def get_all_running(self) -> List[ServiceProcessInfo]:
        """Get all running processes."""
        return list(self._processes.values())
    
    def check_service_health(self, project_id: str, service_id: str) -> tuple[str, Optional[int]]:
        """Check if a service is healthy."""
        key = self._get_key(project_id, service_id)
        proc_info = self._processes.get(key)
        
        if not proc_info:
            return "stopped", None
        
        if proc_info.status != "running":
            return proc_info.status, proc_info.pid
        
        # Check if process is actually alive
        if not self._is_process_alive(proc_info.pid):
            proc_info.status = "crashed"
            proc_info.stopped_at = datetime.now().isoformat()
            return "crashed", proc_info.pid
        
        return "running", proc_info.pid
    
    def check_health(self, project_id: str) -> tuple[str, Optional[int]]:
        """Check health of default service (backward compatibility)."""
        return self.check_service_health(project_id, "default")
    
    def update_service_health(self, project_id: str, service_id: str) -> str:
        """Update and return the health status of a service."""
        status, pid = self.check_service_health(project_id, service_id)
        
        if status == "crashed":
            key = self._get_key(project_id, service_id)
            if key in self._processes:
                proc_info = self._processes[key]
                proc_info.status = "crashed"
        
        return status
    
    def update_health_status(self, project_id: str) -> str:
        """Update health of default service (backward compatibility)."""
        return self.update_service_health(project_id, "default")
    
    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process with given PID is alive."""
        if not pid:
            return False
        
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(pid)
                return process.is_running()
            except psutil.NoSuchProcess:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except (OSError, ProcessLookupError):
                return False
    
    def _terminate_process_tree(self, pid: int, timeout: int = 5) -> bool:
        """Terminate a process and all its children."""
        if not PSUTIL_AVAILABLE:
            return False
        
        try:
            if os.name == 'nt':
                # Windows: Use psutil to terminate process tree
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                
                # First, try to terminate children gracefully
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                
                # Terminate parent
                try:
                    parent.terminate()
                except psutil.NoSuchProcess:
                    pass
                
                # Wait for processes to terminate
                gone, alive = psutil.wait_procs(children + [parent], timeout=timeout)
                
                # Force kill any remaining
                for process in alive:
                    try:
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass
                
                return True
            else:
                # Linux/Mac: Use process groups for signal handling
                try:
                    # Get process group ID (same as PID if start_new_session=True)
                    pgid = os.getpgid(pid)
                    
                    # Send SIGTERM to entire process group
                    os.killpg(pgid, signal.SIGTERM)
                    
                    # Wait a bit for graceful termination
                    time.sleep(timeout)
                    
                    # Check if still alive
                    if self._is_process_alive(pid):
                        # Force kill with SIGKILL
                        os.killpg(pgid, signal.SIGKILL)
                    
                    return True
                except ProcessLookupError:
                    return True  # Process already gone
                except PermissionError:
                    print(f"Permission denied when trying to kill process group {pid}")
                    return False
                except Exception as e:
                    print(f"Error killing process group: {e}")
                    return False
            
        except psutil.NoSuchProcess:
            return True  # Process already gone
        except Exception as e:
            print(f"Error terminating process tree: {e}")
            return False
    
    def cleanup_dead_processes(self):
        """Remove crashed processes from tracking."""
        with self._lock:
            to_remove = []
            for key, proc_info in self._processes.items():
                if proc_info.status == "crashed":
                    if proc_info.stopped_at:
                        to_remove.append(key)
                elif proc_info.status == "running":
                    if not self._is_process_alive(proc_info.pid):
                        proc_info.status = "crashed"
                        proc_info.stopped_at = datetime.now().isoformat()
            
            for key in to_remove:
                del self._processes[key]


# Singleton instance
_process_service = None


def get_process_service() -> ProcessService:
    """Get the singleton process service instance."""
    global _process_service
    if _process_service is None:
        _process_service = ProcessService()
    return _process_service
