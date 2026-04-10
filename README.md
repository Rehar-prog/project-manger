# Project Control Dashboard

A production-ready project manager for Windows and Linux with proper process control, health monitoring, and a modern dashboard interface.

## Features

- **Project Management**: Add, edit, and manage multiple projects
- **Process Control**: Start, stop, and restart projects with proper process management
- **Auto/Manual Mode**: Set projects to auto-start on manager launch
- **Health Monitoring**: Track project status (running, stopped, crashed)
- **System Dashboard**: View CPU, memory, disk usage, and uptime
- **Modern UI**: Dark theme with responsive design
- **REST API**: Full API for external control (e.g., OpenClaw integration)

## Installation

### Windows

1. **Install Python 3.8 or higher**
   - Download from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```
   Or use the batch file:
   ```bash
   run_manager.bat
   ```

4. **Open the dashboard**
   - Navigate to `http://localhost:8787` in your browser

### Linux (Ubuntu/Debian)

1. **Install Python 3.8+ and pip**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **Clone/download the project to your desired location**
   ```bash
   cd /path/to/your/projects
   # Extract or clone the project here
   cd project_runner_manager
   ```

3. **Run with the startup script**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   Or manually:
   ```bash
   pip3 install -r requirements.txt
   python3 app.py
   ```

4. **Open the dashboard**
   - Navigate to `http://localhost:8787` in your browser

## Windows Startup

To make the Project Manager start automatically when Windows boots:

### Option 1: PowerShell Script (Recommended)
1. Right-click on `install_startup_task.ps1`
2. Select "Run with PowerShell"
3. Accept the UAC prompt to run as Administrator

### Option 2: Startup Folder
1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `run_manager.bat`
3. Place the shortcut in the Startup folder

## Linux Auto-Start (systemd)

To make the Project Control Dashboard start automatically when your Linux system boots:

### Step 1: Edit the service file

Open `project-manager.service` and replace the placeholders:

- Replace `YOUR_USERNAME` with your actual username (e.g., `john`)
- Replace `YOUR_PROJECT_PATH` with the full path to the project (e.g., `/home/john/projects/project_runner_manager`)

Example:
```ini
User=john
WorkingDirectory=/home/john/projects/project_runner_manager
ExecStart=/usr/bin/python3 /home/john/projects/project_runner_manager/app.py
```

### Step 2: Copy the service file to systemd

```bash
sudo cp project-manager.service /etc/systemd/system/
```

### Step 3: Enable and start the service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable project-manager

# Start the service immediately
sudo systemctl start project-manager
```

### Step 4: Verify it's running

```bash
# Check service status
sudo systemctl status project-manager

# View logs
sudo journalctl -u project-manager -f
```

### Managing the service

```bash
# Start
sudo systemctl start project-manager

# Stop
sudo systemctl stop project-manager

# Restart
sudo systemctl restart project-manager

# Disable auto-start
sudo systemctl disable project-manager
```

## Usage

### Adding a Project

1. Click the "Add Project" button
2. Fill in the details:
   - **Project Name**: A friendly name for the project
   - **Directory**: The working directory (use clipboard button to paste from File Explorer)
   - **Start Command**: The command to run (e.g., `python app.py`, `npm start`)
   - **Stop Command** (optional): Custom command to stop the project
   - **Mode**: Choose "Auto" to start on manager launch, or "Manual" to control manually
3. Click "Create Project"

### Managing Projects

- **Start**: Start a stopped project
- **Stop**: Stop a running project (properly terminates process tree)
- **Restart**: Stop and start a project
- **Edit**: Modify project settings
- **Delete**: Remove a project (will stop if running)

### Dashboard

The System Dashboard shows:
- Total projects count
- Running/stopped/crashed counts
- CPU, memory, and disk usage
- Running processes with details
- Manager uptime

### Settings

Configure:
- Auto-refresh interval
- Whether to auto-start auto projects
- Toast notifications
- API information for external integration

## API Endpoints

The following REST API endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET | List all projects |
| `/api/projects` | POST | Create a new project |
| `/api/projects/<id>` | GET | Get project details |
| `/api/projects/<id>` | PUT | Update project |
| `/api/projects/<id>` | DELETE | Delete project |
| `/api/projects/<id>/start` | POST | Start a project |
| `/api/projects/<id>/stop` | POST | Stop a project |
| `/api/projects/<id>/restart` | POST | Restart a project |
| `/api/projects/<id>/mode` | POST | Set project mode |
| `/api/projects/<id>/status` | GET | Get detailed status |
| `/api/system/summary` | GET | Get system summary |
| `/api/system/metrics` | GET | Get system metrics |
| `/api/system/processes` | GET | List all system processes |

## Project Configuration

Projects are stored in `projects.json` with the following structure:

```json
{
  "id": "abc123",
  "name": "My Project",
  "dir": "C:\\path\\to\\project",
  "start_cmd": "python app.py",
  "stop_cmd": "",
  "mode": "auto",
  "last_status": "running",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00"
}
```

## Architecture

```
app.py                  # Flask application with API endpoints
├── services/
│   ├── project_service.py    # Project storage and CRUD
│   ├── process_service.py    # Process lifecycle management
│   ├── system_service.py     # System monitoring
│   └── health_monitor.py     # Background health checks
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   └── settings.html
└── static/
    ├── css/style.css
    └── js/
        ├── app.js
        ├── projects.js
        └── dashboard.js
```

## Process Management

The Project Manager uses `psutil` for robust process control on Windows and Linux:

- **Start**: Creates a new process with proper process group/session handling
  - Windows: Uses `CREATE_NEW_PROCESS_GROUP` flag
  - Linux: Uses `start_new_session=True` to create new process group
- **Stop**: 
  1. Attempts custom stop command if provided
  2. Gracefully terminates the process tree/process group
  3. Force kills remaining processes after timeout (SIGKILL on Linux)
- **Health Check**: Monitors processes every 5 seconds

## Troubleshooting

### Projects not auto-starting
- Check the project mode is set to "Auto"
- Check the directory exists and is accessible
- Check the start command is correct
- View console output for errors

### Stop button not working
- The stop button now properly terminates process trees using psutil
- If a process persists, it may require manual termination via Task Manager

### High CPU/Memory usage
- Adjust the refresh interval in Settings
- Reduce the number of running projects
- Check individual process resource usage in the Dashboard

### Cannot access dashboard
- Ensure port 8787 is not blocked by firewall
- Try accessing `http://127.0.0.1:8787` instead
- Check that the Flask app is running

## Security Notes

- The dashboard runs on localhost only (not accessible from network)
- No authentication is implemented (designed for local use)
- Projects run with the same permissions as the manager
- Be cautious when running commands from untrusted sources

## License

MIT License - Feel free to modify and distribute.

## Changelog

### Version 2.0
- Complete rewrite with clean architecture
- Proper process management with psutil
- Modern dark UI with Bootstrap 5
- System monitoring dashboard
- Health monitoring with automatic crash detection
- REST API for external control
- Windows startup task support
"# project-manger" 
