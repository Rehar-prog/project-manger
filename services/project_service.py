"""
Project Service - Manages project storage, CRUD operations, and project state.
Supports multi-service projects with safe backward compatibility.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

PROJECTS_FILE = "projects.json"
SETTINGS_FILE = "settings.json"


class Service:
    """Represents a service (command) within a project."""
    
    def __init__(self, data: Dict[str, Any], project_dir: str = ""):
        self.id = data.get("id") or "default"
        self.name = data.get("name", "Main")
        self.cmd = data.get("cmd") or data.get("start_cmd", "")
        self.dir = data.get("dir") or project_dir  # Can override project dir
        self.stop_cmd = data.get("stop_cmd", "")
        self.status = data.get("status", "stopped")
        self.pid = data.get("pid", None)
        self.started_at = data.get("started_at", None)
        self.stopped_at = data.get("stopped_at", None)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "cmd": self.cmd,
            "dir": self.dir,
            "stop_cmd": self.stop_cmd,
            "status": self.status,
            "pid": self.pid,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at
        }


class Project:
    """Represents a project with all its configuration and runtime state.
    
    Backward Compatibility:
    - Old projects with single cmd are auto-migrated to have one default service
    - All existing fields are preserved
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id") or str(uuid.uuid4())[:8]
        self.name = data.get("name", "Unnamed Project")
        self.dir = data.get("dir", "")
        
        # Legacy fields for backward compatibility
        self.start_cmd = data.get("start_cmd") or data.get("cmd", "")
        self.stop_cmd = data.get("stop_cmd", "")
        
        # Mode and status
        self.mode = data.get("mode", "manual")  # "auto" or "manual"
        self.last_status = data.get("last_status", "stopped")
        
        # Timestamps
        self.created_at = data.get("created_at", datetime.now().isoformat())
        self.updated_at = data.get("updated_at", datetime.now().isoformat())
        self.started_at = data.get("started_at", None)
        self.stopped_at = data.get("stopped_at", None)
        self.pid = data.get("pid", None)  # Legacy PID for backward compat
        
        # Multi-service support
        # If services array exists, use it; otherwise create default service from legacy fields
        if "services" in data and isinstance(data["services"], list) and len(data["services"]) > 0:
            self.services = [Service(s, self.dir) for s in data["services"]]
        else:
            # Create default service from legacy fields
            default_service_data = {
                "id": "default",
                "name": "Main",
                "cmd": self.start_cmd,
                "dir": self.dir,
                "stop_cmd": self.stop_cmd,
                "status": self.last_status,
                "pid": self.pid,
                "started_at": self.started_at,
                "stopped_at": self.stopped_at
            }
            self.services = [Service(default_service_data, self.dir)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for storage."""
        # Get primary service for backward compatibility
        primary_service = self.services[0] if self.services else None
        
        return {
            "id": self.id,
            "name": self.name,
            "dir": self.dir,
            "start_cmd": self.start_cmd,
            "stop_cmd": self.stop_cmd,
            "mode": self.mode,
            "last_status": self.last_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "pid": self.pid,
            "services": [s.to_dict() for s in self.services]
        }
    
    def get_primary_service(self) -> Optional[Service]:
        """Get the primary (first) service - for backward compatibility."""
        return self.services[0] if self.services else None
    
    def get_service(self, service_id: str) -> Optional[Service]:
        """Get a service by ID."""
        for service in self.services:
            if service.id == service_id:
                return service
        return None
    
    def add_service(self, service_data: Dict[str, Any]) -> Service:
        """Add a new service to the project."""
        service_data["id"] = service_data.get("id") or f"svc_{len(self.services)}"
        service = Service(service_data, self.dir)
        self.services.append(service)
        self.updated_at = datetime.now().isoformat()
        return service
    
    def remove_service(self, service_id: str) -> bool:
        """Remove a service from the project."""
        if len(self.services) <= 1:
            return False  # Can't remove the last service
        
        for i, service in enumerate(self.services):
            if service.id == service_id:
                self.services.pop(i)
                self.updated_at = datetime.now().isoformat()
                return True
        return False
    
    def update_service(self, service_id: str, data: Dict[str, Any]) -> bool:
        """Update a service."""
        service = self.get_service(service_id)
        if not service:
            return False
        
        if "name" in data:
            service.name = data["name"]
        if "cmd" in data or "start_cmd" in data:
            service.cmd = data.get("cmd") or data.get("start_cmd", service.cmd)
        if "dir" in data:
            service.dir = data["dir"]
        if "stop_cmd" in data:
            service.stop_cmd = data["stop_cmd"]
        if "status" in data:
            service.status = data["status"]
        if "pid" in data:
            service.pid = data["pid"]
        if "started_at" in data:
            service.started_at = data["started_at"]
        if "stopped_at" in data:
            service.stopped_at = data["stopped_at"]
        
        self.updated_at = datetime.now().isoformat()
        
        # Sync with legacy fields if this is the primary service
        if service_id == "default" or service == self.services[0]:
            self.start_cmd = service.cmd
            self.stop_cmd = service.stop_cmd
            self.last_status = service.status
            self.pid = service.pid
            self.started_at = service.started_at
            self.stopped_at = service.stopped_at
        
        return True
    
    def validate(self) -> tuple[bool, str]:
        """Validate project configuration."""
        if not self.name or not self.name.strip():
            return False, "Project name is required"
        
        if not self.dir or not self.dir.strip():
            return False, "Project directory is required"
        
        if not os.path.exists(self.dir):
            return False, f"Directory does not exist: {self.dir}"
        
        # Validate all services have commands
        for service in self.services:
            if not service.cmd or not service.cmd.strip():
                return False, f"Service '{service.name}' is missing a command"
        
        return True, ""
    
    def get_overall_status(self) -> str:
        """Get overall project status based on services."""
        if not self.services:
            return "stopped"
        
        statuses = [s.status for s in self.services]
        
        if all(s == "running" for s in statuses):
            return "running"
        elif any(s == "crashed" for s in statuses):
            return "crashed"
        elif any(s == "running" for s in statuses):
            return "partial"  # Some running, some not
        else:
            return "stopped"


class ProjectService:
    """Service for managing projects."""
    
    def __init__(self, data_file: str = PROJECTS_FILE):
        self.data_file = data_file
        self._projects: Dict[str, Project] = {}
        self._load()
    
    def _load(self):
        """Load projects from file."""
        if not os.path.exists(self.data_file):
            self._projects = {}
            return
        
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
            
            self._projects = {}
            for proj_data in data:
                project = Project(proj_data)
                self._projects[project.id] = project
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading projects: {e}")
            self._projects = {}
    
    def _save(self):
        """Save projects to file."""
        data = [p.to_dict() for p in self._projects.values()]
        try:
            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving projects: {e}")
    
    def get_all(self) -> List[Project]:
        """Get all projects."""
        return list(self._projects.values())
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self._projects.get(project_id)
    
    def create(self, data: Dict[str, Any]) -> tuple[Project, str]:
        """Create a new project."""
        project = Project(data)
        
        # Validate
        is_valid, error = project.validate()
        if not is_valid:
            return None, error
        
        # Check for duplicate name
        for existing in self._projects.values():
            if existing.name.lower() == project.name.lower():
                return None, f"Project with name '{project.name}' already exists"
        
        project.updated_at = datetime.now().isoformat()
        self._projects[project.id] = project
        self._save()
        
        return project, ""
    
    def update(self, project_id: str, data: Dict[str, Any]) -> tuple[Optional[Project], str]:
        """Update an existing project."""
        project = self._projects.get(project_id)
        if not project:
            return None, f"Project not found: {project_id}"
        
        # Update fields
        if "name" in data:
            project.name = data["name"]
        if "dir" in data:
            project.dir = data["dir"]
            # Update default service dir too
            for service in project.services:
                if service.id == "default":
                    service.dir = data["dir"]
        if "start_cmd" in data:
            project.start_cmd = data["start_cmd"]
            # Update default service
            if project.services:
                project.services[0].cmd = data["start_cmd"]
        if "cmd" in data:  # Support old field name
            project.start_cmd = data["cmd"]
            if project.services:
                project.services[0].cmd = data["cmd"]
        if "stop_cmd" in data:
            project.stop_cmd = data["stop_cmd"]
            if project.services:
                project.services[0].stop_cmd = data["stop_cmd"]
        if "mode" in data:
            project.mode = data["mode"]
        if "last_status" in data:
            project.last_status = data["last_status"]
        if "pid" in data:
            project.pid = data["pid"]
        if "started_at" in data:
            project.started_at = data["started_at"]
        if "stopped_at" in data:
            project.stopped_at = data["stopped_at"]
        if "services" in data:
            # Update services
            project.services = [Service(s, project.dir) for s in data["services"]]
        
        # Validate
        is_valid, error = project.validate()
        if not is_valid:
            return None, error
        
        project.updated_at = datetime.now().isoformat()
        self._save()
        
        return project, ""
    
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id not in self._projects:
            return False
        del self._projects[project_id]
        self._save()
        return True
    
    def get_auto_projects(self) -> List[Project]:
        """Get all projects in auto mode."""
        return [p for p in self._projects.values() if p.mode == "auto"]
    
    def toggle_mode(self, project_id: str) -> tuple[Optional[str], str]:
        """Toggle project mode between auto and manual."""
        project = self._projects.get(project_id)
        if not project:
            return None, f"Project not found: {project_id}"
        
        # Toggle mode
        new_mode = "manual" if project.mode == "auto" else "auto"
        project.mode = new_mode
        project.updated_at = datetime.now().isoformat()
        self._save()
        
        return new_mode, ""
    
    def update_status(self, project_id: str, status: str, pid: int = None, 
                      started_at: str = None, stopped_at: str = None,
                      service_id: str = None):
        """Update project status and runtime info."""
        project = self._projects.get(project_id)
        if not project:
            return
        
        if service_id:
            # Update specific service
            service = project.get_service(service_id)
            if service:
                service.status = status
                if pid is not None:
                    service.pid = pid
                if started_at is not None:
                    service.started_at = started_at
                if stopped_at is not None:
                    service.stopped_at = stopped_at
        else:
            # Update legacy fields and primary service
            project.last_status = status
            if pid is not None:
                project.pid = pid
            if started_at is not None:
                project.started_at = started_at
            if stopped_at is not None:
                project.stopped_at = stopped_at
            
            # Sync with primary service
            if project.services:
                project.services[0].status = status
                project.services[0].pid = pid
                project.services[0].started_at = started_at
                project.services[0].stopped_at = stopped_at
        
        project.updated_at = datetime.now().isoformat()
        self._save()
    
    def migrate_from_old_format(self):
        """Migrate old projects.json format to new format with services."""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return
            
            needs_migration = False
            migrated_count = 0
            
            for proj in data:
                # Check if needs migration to services format
                if "services" not in proj:
                    needs_migration = True
                    
                    # Create default service from legacy fields
                    default_service = {
                        "id": "default",
                        "name": "Main",
                        "cmd": proj.get("start_cmd") or proj.get("cmd", ""),
                        "dir": proj.get("dir", ""),
                        "stop_cmd": proj.get("stop_cmd", ""),
                        "status": proj.get("last_status", "stopped"),
                        "pid": proj.get("pid", None),
                        "started_at": proj.get("started_at", None),
                        "stopped_at": proj.get("stopped_at", None)
                    }
                    
                    proj["services"] = [default_service]
                    migrated_count += 1
                
                # Legacy field migrations
                if "cmd" in proj and "start_cmd" not in proj:
                    proj["start_cmd"] = proj.pop("cmd")
                    needs_migration = True
                
                if isinstance(proj.get("id"), int):
                    proj["id"] = str(uuid.uuid4())[:8]
                    needs_migration = True
                
                # Ensure all fields exist
                for field, default in [
                    ("stop_cmd", ""),
                    ("last_status", "stopped"),
                    ("created_at", datetime.now().isoformat()),
                    ("updated_at", datetime.now().isoformat()),
                    ("started_at", None),
                    ("stopped_at", None),
                    ("pid", None)
                ]:
                    if field not in proj:
                        proj[field] = default
                        needs_migration = True
            
            if needs_migration:
                print(f"Migrating {migrated_count} projects to new format...")
                with open(self.data_file, "w") as f:
                    json.dump(data, f, indent=2)
                print("Migration complete.")
                self._load()
        except Exception as e:
            print(f"Migration error: {e}")


class SettingsService:
    """Service for managing application settings."""
    
    def __init__(self, settings_file: str = SETTINGS_FILE):
        self.settings_file = settings_file
        self._settings = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            return self._get_defaults()
        
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
            # Merge with defaults for any missing keys
            defaults = self._get_defaults()
            defaults.update(settings)
            return defaults
        except (json.JSONDecodeError, IOError):
            return self._get_defaults()
    
    def _save(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self._settings, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            "theme": "dark",
            "refresh_interval": 5,
            "auto_start_projects": True,
            "minimize_logging": False,
            "show_notifications": True
        }
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    def set(self, key: str, value: Any):
        """Set a setting value."""
        self._settings[key] = value
        self._save()
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple settings."""
        self._settings.update(updates)
        self._save()


# Singleton instances
_project_service = None
_settings_service = None


def get_project_service() -> ProjectService:
    """Get the singleton project service instance."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
        _project_service.migrate_from_old_format()
    return _project_service


def get_settings_service() -> SettingsService:
    """Get the singleton settings service instance."""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
