"""
Project Control Dashboard - Flask Application
A production-ready project manager with proper process control, monitoring,
multi-service support, and theme management.
"""
import os
import sys
import argparse
import webbrowser
from datetime import datetime
from flask import Flask, request, jsonify, render_template, render_template_string

# Add services to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.project_service import get_project_service, get_settings_service
from services.process_service import get_process_service
from services.system_service import get_system_service
from services.health_monitor import get_health_monitor

app = Flask(__name__)

# Initialize services
project_service = get_project_service()
process_service = get_process_service()
system_service = get_system_service()
settings_service = get_settings_service()

# Health monitor will be started after app initialization
health_monitor = None

# Store system metrics history for charts
metrics_history = {
    "cpu": [],
    "memory": [],
    "timestamps": []
}
MAX_HISTORY = 60  # Keep last 60 data points

# =============================================================================
# WEB ROUTES
# =============================================================================

@app.route("/")
def index():
    """Main dashboard page."""
    theme = settings_service.get("theme", "dark")
    return render_template("index.html", theme=theme)


@app.route("/dashboard")
def dashboard():
    """Dashboard view."""
    theme = settings_service.get("theme", "dark")
    return render_template("dashboard.html", theme=theme)


@app.route("/settings")
def settings_page():
    """Settings page."""
    theme = settings_service.get("theme", "dark")
    settings = settings_service.get_all()
    return render_template("settings.html", theme=theme, settings=settings)


# =============================================================================
# API ENDPOINTS - SETTINGS
# =============================================================================

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get all settings."""
    try:
        return jsonify(settings_service.get_all())
    except Exception as e:
        print(f"[ERROR] get_settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/settings", methods=["PUT"])
def update_settings():
    """Update settings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        settings_service.update(data)
        return jsonify({
            "success": True,
            "message": "Settings updated",
            "settings": settings_service.get_all()
        })
    except Exception as e:
        print(f"[ERROR] update_settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/settings/theme", methods=["POST"])
def set_theme():
    """Set application theme."""
    try:
        data = request.get_json()
        theme = data.get("theme")
        
        if theme not in ["dark", "light"]:
            return jsonify({"success": False, "error": "Invalid theme"}), 400
        
        settings_service.set("theme", theme)
        return jsonify({
            "success": True,
            "message": f"Theme set to {theme}",
            "theme": theme
        })
    except Exception as e:
        print(f"[ERROR] set_theme: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# API ENDPOINTS - PROJECTS
# =============================================================================

@app.route("/api/projects", methods=["GET"])
def get_projects():
    """Get all projects with their current status."""
    try:
        projects = project_service.get_all()
        result = []
        
        for project in projects:
            try:
                # Get runtime status for each service
                services_status = []
                for service in project.services:
                    try:
                        status, pid = process_service.check_service_health(project.id, service.id)
                        proc_info = process_service.get_service_info(project.id, service.id)
                        
                        # Calculate uptime if running
                        uptime = None
                        if proc_info and proc_info.started_at and status == "running":
                            try:
                                started = datetime.fromisoformat(proc_info.started_at)
                                uptime_seconds = (datetime.now() - started).total_seconds()
                                uptime = format_duration(uptime_seconds)
                            except:
                                uptime = None
                        
                        services_status.append({
                            "id": service.id,
                            "name": service.name,
                            "cmd": service.cmd,
                            "dir": service.dir,
                            "status": status,
                            "pid": pid,
                            "uptime": uptime
                        })
                    except Exception as e:
                        print(f"[ERROR] Processing service {service.id} for project {project.id}: {e}")
                        services_status.append({
                            "id": service.id,
                            "name": service.name,
                            "cmd": service.cmd,
                            "dir": service.dir,
                            "status": "error",
                            "pid": None,
                            "uptime": None
                        })
                
                # Determine overall health status
                overall_status = project.get_overall_status()
                
                # Get primary service info for backward compatibility
                primary = services_status[0] if services_status else None
                
                result.append({
                    "id": project.id,
                    "name": project.name,
                    "dir": project.dir,
                    "mode": project.mode,
                    "status": overall_status,
                    "services_count": len(project.services),
                    "services": services_status,
                    "start_cmd": project.start_cmd,
                    "stop_cmd": project.stop_cmd,
                    "pid": primary["pid"] if primary else None,
                    "uptime": primary["uptime"] if primary else None,
                    "created_at": project.created_at,
                    "updated_at": project.updated_at,
                    "started_at": project.started_at,
                    "stopped_at": project.stopped_at
                })
            except Exception as e:
                print(f"[ERROR] Processing project {project.id}: {e}")
                import traceback
                traceback.print_exc()
                # Skip this project but continue with others
                continue
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"[ERROR] get_projects: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects", methods=["POST"])
def add_project():
    """Create a new project."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Validate required fields
        required = ["name", "dir"]
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        # Handle services or legacy single command
        if "services" in data and isinstance(data["services"], list) and len(data["services"]) > 0:
            # Multi-service project
            pass
        else:
            # Legacy single command project or missing services
            if "start_cmd" not in data or not data["start_cmd"]:
                return jsonify({"success": False, "error": "Missing required field: command"}), 400
            
            # Create default service
            data["services"] = [{
                "id": "default",
                "name": "Main",
                "cmd": data["start_cmd"],
                "dir": data["dir"],
                "stop_cmd": data.get("stop_cmd", "")
            }]
        
        # Set default mode
        if "mode" not in data:
            data["mode"] = "manual"
        
        # Create project
        print(f"[CREATE_PROJECT] Creating project with data: {data}")
        project, error = project_service.create(data)
        
        if error:
            print(f"[CREATE_PROJECT] Validation error: {error}")
            return jsonify({"success": False, "error": error}), 400
        
        return jsonify({
            "success": True,
            "message": "Project created successfully",
            "project": project.to_dict()
        })
    except Exception as e:
        print(f"[ERROR] add_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """Get a specific project."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        return jsonify({"success": True, "data": project.to_dict()})
    except Exception as e:
        print(f"[ERROR] get_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    """Update a project."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        project, error = project_service.update(project_id, data)
        
        if error:
            if "not found" in error.lower():
                return jsonify({"success": False, "error": error}), 404
            return jsonify({"success": False, "error": error}), 400
        
        return jsonify({
            "success": True,
            "message": "Project updated successfully",
            "project": project.to_dict()
        })
    except Exception as e:
        print(f"[ERROR] update_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """Delete a project."""
    try:
        project = project_service.get_by_id(project_id)
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        # Stop all services first
        for service in project.services:
            try:
                process_service.stop_service(project_id, service.id, service.stop_cmd, service.dir)
            except Exception as e:
                print(f"[WARN] Failed to stop service {service.id}: {e}")
        
        # Then delete
        success = project_service.delete(project_id)
        
        if not success:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        return jsonify({
            "success": True,
            "message": "Project deleted successfully"
        })
    except Exception as e:
        print(f"[ERROR] delete_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# API ENDPOINTS - PROJECT ACTIONS
# =============================================================================

@app.route("/api/projects/<project_id>/start", methods=["POST"])
def start_project(project_id):
    """Start all services in a project."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        started_services = []
        failed_services = []
        
        for service in project.services:
            try:
                # Check if already running
                status, _ = process_service.check_service_health(project_id, service.id)
                if status == "running":
                    started_services.append(service.name)
                    continue
                
                # Start the service
                success, message, proc_info = process_service.start_service(
                    project_id,
                    service.id,
                    service.dir,
                    service.cmd
                )
                
                if success:
                    project_service.update_status(
                        project_id,
                        "running",
                        pid=proc_info.pid,
                        started_at=proc_info.started_at,
                        service_id=service.id
                    )
                    started_services.append(service.name)
                else:
                    project_service.update_status(
                        project_id,
                        "crashed",
                        service_id=service.id
                    )
                    failed_services.append({"name": service.name, "error": message})
            except Exception as e:
                print(f"[ERROR] Starting service {service.id}: {e}")
                failed_services.append({"name": service.name, "error": str(e)})
        
        if failed_services and not started_services:
            return jsonify({
                "success": False,
                "message": "Failed to start all services",
                "failed": failed_services
            }), 500
        
        return jsonify({
            "success": True,
            "message": f"Started {len(started_services)} service(s)",
            "started": started_services,
            "failed": failed_services
        })
    except Exception as e:
        print(f"[ERROR] start_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/stop", methods=["POST"])
def stop_project(project_id):
    """Stop all services in a project."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        stopped_services = []
        
        for service in project.services:
            try:
                success, message = process_service.stop_service(
                    project_id,
                    service.id,
                    service.stop_cmd,
                    service.dir
                )
                
                # Update project status
                project_service.update_status(
                    project_id,
                    "stopped",
                    pid=None,
                    stopped_at=datetime.now().isoformat(),
                    service_id=service.id
                )
                
                stopped_services.append(service.name)
            except Exception as e:
                print(f"[ERROR] Stopping service {service.id}: {e}")
        
        return jsonify({
            "success": True,
            "message": f"Stopped {len(stopped_services)} service(s)",
            "stopped": stopped_services
        })
    except Exception as e:
        print(f"[ERROR] stop_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/restart", methods=["POST"])
def restart_project(project_id):
    """Restart all services in a project."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        # Stop all first
        for service in project.services:
            try:
                process_service.stop_service(project_id, service.id, service.stop_cmd, service.dir)
            except Exception as e:
                print(f"[WARN] Failed to stop service {service.id}: {e}")
        
        import time
        time.sleep(0.5)
        
        # Start all
        started_services = []
        failed_services = []
        
        for service in project.services:
            try:
                success, message, proc_info = process_service.restart_service(
                    project_id,
                    service.id,
                    service.dir,
                    service.cmd,
                    service.stop_cmd
                )
                
                if success and proc_info:
                    project_service.update_status(
                        project_id,
                        "running",
                        pid=proc_info.pid,
                        started_at=proc_info.started_at,
                        service_id=service.id
                    )
                    started_services.append(service.name)
                else:
                    project_service.update_status(
                        project_id,
                        "crashed",
                        service_id=service.id
                    )
                    failed_services.append({"name": service.name, "error": message})
            except Exception as e:
                print(f"[ERROR] Restarting service {service.id}: {e}")
                failed_services.append({"name": service.name, "error": str(e)})
        
        if failed_services and not started_services:
            return jsonify({
                "success": False,
                "message": "Failed to restart all services",
                "failed": failed_services
            }), 500
        
        return jsonify({
            "success": True,
            "message": f"Restarted {len(started_services)} service(s)",
            "started": started_services,
            "failed": failed_services
        })
    except Exception as e:
        print(f"[ERROR] restart_project: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/toggle-mode", methods=["POST"])
def toggle_project_mode(project_id):
    """Toggle project mode between auto and manual."""
    try:
        new_mode, error = project_service.toggle_mode(project_id)
        
        if error:
            if "not found" in error.lower():
                return jsonify({"success": False, "error": error}), 404
            return jsonify({"success": False, "error": error}), 400
        
        return jsonify({
            "success": True,
            "message": f"Mode toggled to {new_mode}",
            "mode": new_mode
        })
    except Exception as e:
        print(f"[ERROR] toggle_project_mode: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# API ENDPOINTS - SERVICE ACTIONS
# =============================================================================

@app.route("/api/projects/<project_id>/services/<service_id>/start", methods=["POST"])
def start_service(project_id, service_id):
    """Start a specific service."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        service = project.get_service(service_id)
        if not service:
            return jsonify({"success": False, "error": "Service not found"}), 404
        
        # Check if already running
        status, _ = process_service.check_service_health(project_id, service_id)
        if status == "running":
            return jsonify({"success": True, "message": "Service already running"})
        
        # Start the service
        success, message, proc_info = process_service.start_service(
            project_id,
            service_id,
            service.dir,
            service.cmd
        )
        
        if success:
            project_service.update_status(
                project_id,
                "running",
                pid=proc_info.pid,
                started_at=proc_info.started_at,
                service_id=service_id
            )
            
            return jsonify({
                "success": True,
                "message": message,
                "pid": proc_info.pid
            })
        else:
            project_service.update_status(project_id, "crashed", service_id=service_id)
            return jsonify({"success": False, "error": message}), 500
    except Exception as e:
        print(f"[ERROR] start_service: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/<project_id>/services/<service_id>/stop", methods=["POST"])
def stop_service(project_id, service_id):
    """Stop a specific service."""
    try:
        project = project_service.get_by_id(project_id)
        
        if not project:
            return jsonify({"success": False, "error": "Project not found"}), 404
        
        service = project.get_service(service_id)
        if not service:
            return jsonify({"success": False, "error": "Service not found"}), 404
        
        success, message = process_service.stop_service(
            project_id,
            service_id,
            service.stop_cmd,
            service.dir
        )
        
        project_service.update_status(
            project_id,
            "stopped",
            pid=None,
            stopped_at=datetime.now().isoformat(),
            service_id=service_id
        )
        
        return jsonify({
            "success": True,
            "message": message
        })
    except Exception as e:
        print(f"[ERROR] stop_service: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# API ENDPOINTS - SYSTEM
# =============================================================================

@app.route("/api/system/summary", methods=["GET"])
def get_system_summary():
    """Get system summary including project counts and metrics."""
    try:
        projects = project_service.get_all()
        metrics = system_service.get_cached_metrics()
        
        # Count projects by status
        running_count = 0
        stopped_count = 0
        crashed_count = 0
        
        for project in projects:
            status = project.get_overall_status()
            if status == "running":
                running_count += 1
            elif status == "crashed":
                crashed_count += 1
            else:
                stopped_count += 1
        
        # Update metrics history
        global metrics_history
        current_time = datetime.now().strftime("%H:%M:%S")
        
        metrics_history["cpu"].append(metrics.get("cpu_percent", 0))
        metrics_history["memory"].append(metrics.get("memory_percent", 0))
        metrics_history["timestamps"].append(current_time)
        
        # Keep only last MAX_HISTORY points
        if len(metrics_history["cpu"]) > MAX_HISTORY:
            metrics_history["cpu"] = metrics_history["cpu"][-MAX_HISTORY:]
            metrics_history["memory"] = metrics_history["memory"][-MAX_HISTORY:]
            metrics_history["timestamps"] = metrics_history["timestamps"][-MAX_HISTORY:]
        
        return jsonify({
            "success": True,
            "projects": {
                "total": len(projects),
                "running": running_count,
                "stopped": stopped_count,
                "crashed": crashed_count,
                "auto": len([p for p in projects if p.mode == "auto"]),
                "manual": len([p for p in projects if p.mode == "manual"])
            },
            "system": metrics,
            "history": metrics_history
        })
    except Exception as e:
        print(f"[ERROR] get_system_summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/metrics", methods=["GET"])
def get_system_metrics():
    """Get system metrics."""
    try:
        return jsonify(system_service.get_cached_metrics())
    except Exception as e:
        print(f"[ERROR] get_system_metrics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/history", methods=["GET"])
def get_system_history():
    """Get system metrics history for charts."""
    try:
        return jsonify(metrics_history)
    except Exception as e:
        print(f"[ERROR] get_system_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/validate-directory", methods=["POST"])
def validate_directory():
    """Validate if a directory exists."""
    try:
        data = request.get_json()
        path = data.get("path", "")
        
        exists = os.path.exists(path) and os.path.isdir(path)
        
        return jsonify({
            "success": True,
            "valid": exists,
            "path": path,
            "error": None if exists else "Directory does not exist"
        })
    except Exception as e:
        print(f"[ERROR] validate_directory: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def auto_start_projects():
    """Auto-start all projects set to auto mode."""
    try:
        if not settings_service.get("auto_start_projects", True):
            print("Auto-start disabled in settings")
            return
        
        auto_projects = project_service.get_auto_projects()
        print(f"Auto-starting {len(auto_projects)} projects...")
        
        for project in auto_projects:
            try:
                print(f"  Starting {project.name}...")
                
                for service in project.services:
                    try:
                        success, message, proc_info = process_service.start_service(
                            project.id,
                            service.id,
                            service.dir,
                            service.cmd
                        )
                        
                        if success:
                            project_service.update_status(
                                project.id,
                                "running",
                                pid=proc_info.pid,
                                started_at=proc_info.started_at,
                                service_id=service.id
                            )
                            print(f"  ✓ {service.name} started (PID: {proc_info.pid})")
                        else:
                            print(f"  ✗ {service.name} failed: {message}")
                    except Exception as e:
                        print(f"  ✗ {service.name} error: {e}")
            except Exception as e:
                print(f"  ✗ {project.name} error: {e}")
    except Exception as e:
        print(f"[ERROR] auto_start_projects: {e}")
        import traceback
        traceback.print_exc()


def init_app():
    """Initialize the application."""
    global health_monitor
    
    # Auto-start auto mode projects
    auto_start_projects()
    
    # Start health monitor
    try:
        health_monitor = get_health_monitor(interval=5)
        health_monitor.start()
    except Exception as e:
        print(f"[WARN] Failed to start health monitor: {e}")


@app.before_request
def before_request():
    """Ensure health monitor is running."""
    global health_monitor
    if health_monitor is None or not health_monitor.is_running():
        try:
            health_monitor = get_health_monitor(interval=5)
            health_monitor.start()
        except Exception as e:
            print(f"[WARN] Failed to restart health monitor: {e}")


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404
    return render_template_string("<h1>404 - Page Not Found</h1>"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    print(f"[ERROR] Internal server error: {error}")
    import traceback
    traceback.print_exc()
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return render_template_string("<h1>500 - Internal Server Error</h1>"), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle any unhandled exceptions."""
    print(f"[ERROR] Unhandled exception: {error}")
    import traceback
    traceback.print_exc()
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": str(error)}), 500
    raise error


# =============================================================================
# MAIN
# =============================================================================

def open_browser_delayed(url, delay=2.0):
    """Open browser after a delay to ensure server is ready."""
    import threading
    import time
    
    def open_browser():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Warning: Could not open browser: {e}")
    
    thread = threading.Thread(target=open_browser, daemon=True)
    thread.start()


def show_error_dialog(message, title="Error"):
    """Show native error dialog when Flask fails to start."""
    import platform
    
    system = platform.system()
    
    if system == "Windows":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # 0x10 = Error icon
        except Exception:
            pass
    elif system == "Darwin":  # macOS
        try:
            import subprocess
            script = f'display dialog "{message}" with title "{title}" buttons {{"OK"}} default button "OK" with icon stop'
            subprocess.run(["osascript", "-e", script], capture_output=True)
        except Exception:
            pass
    else:  # Linux
        try:
            import tkinter.messagebox
            import tkinter
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror(title, message)
            root.destroy()
        except Exception:
            pass
    
    # Always print to stderr as fallback
    print(f"\n{title}: {message}\n", file=sys.stderr)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Project Control Dashboard')
    parser.add_argument('--server-only', action='store_true', 
                        help='Run server without opening browser')
    parser.add_argument('--version', action='store_true',
                        help='Show version information')
    args = parser.parse_args()
    
    # Show version if requested
    if args.version:
        try:
            from version import __version__, __app_name__
            print(f"{__app_name__} v{__version__}")
        except ImportError:
            print("Project Manager v2.1.0")
        sys.exit(0)
    
    # Initialize application
    try:
        init_app()
    except Exception as e:
        show_error_dialog(f"Failed to initialize application:\n{str(e)}", 
                         "Initialization Error")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("  Project Control Dashboard")
    print("="*60)
    print("  URL: http://localhost:8787")
    print("  Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    # Open browser automatically (only when frozen/packaged and not --server-only)
    if not args.server_only and getattr(sys, 'frozen', False):
        open_browser_delayed("http://localhost:8787", delay=2.0)
        print("  Opening browser...\n")
    
    # Start Flask server
    try:
        app.run(host="0.0.0.0", port=8787, debug=False, use_reloader=False)
    except Exception as e:
        show_error_dialog(f"Failed to start server:\n{str(e)}\n\n"
                         "Port 8787 may be in use by another application.",
                         "Server Error")
        sys.exit(1)
    finally:
        if health_monitor:
            try:
                health_monitor.stop()
            except:
                pass
