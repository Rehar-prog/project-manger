Name:           projectmanager
Version:        2.1.0
Release:        1%{?dist}
Summary:        Project Control Dashboard

License:        MIT
URL:            https://github.com/reharlab/project-manager

# No Source0 - we use pre-built binary from dist/
# The build process expects the PyInstaller output in %%{sourcedir}/dist/

# Build requirements
BuildArch:      x86_64
BuildRequires:  desktop-file-utils

# Runtime requirements
Requires:       gtk3
Requires:       webkit2gtk3
Recommends:     python3

%description
Production-ready project manager with multi-service support,
theme management, and comprehensive monitoring.

Features include:
- Multi-service project support
- Process lifecycle management  
- System monitoring dashboard
- Auto-start capability
- REST API for external integration

%prep
# No prep needed - using pre-built binary
# Binary should be in %{sourcedir}/dist/ProjectManager/

%build
# No build step - PyInstaller already created the binary

%install
# Create directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}/projectmanager
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/doc/projectmanager

# Check if dist/ProjectManager exists (from PyInstaller)
if [ -d "%{sourcedir}/dist/ProjectManager" ]; then
    # Install all files from PyInstaller dist
    cp -r %{sourcedir}/dist/ProjectManager/* %{buildroot}%{_libdir}/projectmanager/
else
    echo "Error: dist/ProjectManager not found. Run PyInstaller first."
    exit 1
fi

# Install wrapper script
cat > %{buildroot}%{_bindir}/projectmanager << 'EOF'
#!/bin/bash
export PROJECT_MANAGER_HOME="${HOME}/.local/share/projectmanager"
export PROJECT_MANAGER_CONFIG="${HOME}/.config/projectmanager"

mkdir -p "$PROJECT_MANAGER_HOME"
mkdir -p "$PROJECT_MANAGER_CONFIG"

if [ ! -f "$PROJECT_MANAGER_HOME/projects.json" ]; then
    echo '[]' > "$PROJECT_MANAGER_HOME/projects.json"
fi

if [ ! -f "$PROJECT_MANAGER_CONFIG/settings.json" ]; then
    echo '{"theme": "dark", "refresh_interval": 5, "auto_start_projects": false, "show_notifications": true, "minimize_logging": false}' > "$PROJECT_MANAGER_CONFIG/settings.json"
fi

exec %{_libdir}/projectmanager/ProjectManager "$@"
EOF
chmod +x %{buildroot}%{_bindir}/projectmanager

# Install desktop file
cat > %{buildroot}%{_datadir}/applications/projectmanager.desktop << 'EOF'
[Desktop Entry]
Name=Project Manager
Comment=Production-ready project manager with multi-service support
Exec=/usr/bin/projectmanager
Icon=projectmanager
Type=Application
Categories=System;Monitor;Development;
Terminal=false
StartupNotify=true
StartupWMClass=ProjectManager
EOF

# Install icon (placeholder - will be replaced if assets/icon.png exists)
if [ -f "%{sourcedir}/assets/icon.png" ]; then
    cp %{sourcedir}/assets/icon.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/projectmanager.png
else
    # Create a placeholder icon
    touch %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/projectmanager.png
fi

# Install documentation
if [ -f "%{sourcedir}/README.md" ]; then
    cp %{sourcedir}/README.md %{buildroot}%{_datadir}/doc/projectmanager/
fi
if [ -f "%{sourcedir}/LICENSE" ]; then
    cp %{sourcedir}/LICENSE %{buildroot}%{_datadir}/doc/projectmanager/
fi

# Validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/projectmanager.desktop || true

%files
%attr(755, root, root) %{_bindir}/projectmanager
%{_libdir}/projectmanager/
%{_datadir}/applications/projectmanager.desktop
%{_datadir}/icons/hicolor/256x256/apps/projectmanager.png
%doc %{_datadir}/doc/projectmanager/

%changelog
* Thu Jan 23 2025 Rehar.Lab <support@reharlab.com> - 2.1.0-1
- Initial RPM release
- Production-ready project manager
- Multi-service support
- System monitoring dashboard
