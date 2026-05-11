# Project Manager - Distribution & Packaging Guide

This document describes how to build and distribute the Project Manager application for Windows and Linux platforms.

## Overview

The Project Manager is a Python Flask web application packaged as a standalone desktop application using **PyInstaller**. This creates native executables that don't require Python to be installed on the target system.

### Supported Platforms

- **Windows**: 10/11 (x64)
- **Linux**: Ubuntu/Debian (.deb), Fedora/RHEL (.rpm), Universal (AppImage)

## Quick Start

### Build Everything (All Platforms)

```bash
./build.sh all --version 2.1.0
```

### Build Specific Platform

```bash
# Windows only (must run on Windows)
./build.sh windows

# Linux packages only
./build.sh linux

# Individual Linux formats
./build.sh deb      # Debian/Ubuntu
./build.sh rpm      # Fedora/RHEL
./build.sh appimage # Universal AppImage
```

### Clean Build Artifacts

```bash
./build.sh clean
```

## Build System Architecture

```
build.sh (Unified build script)
    ├── PyInstaller (creates standalone executable)
    │   └── ProjectManager.spec
    ├── Windows
    │   └── Inno Setup → .exe installer
    │       └── installer.iss
    └── Linux
        ├── dpkg-deb → .deb package
        │   └── packaging/debian/
        ├── rpmbuild → .rpm package
        │   └── packaging/rpm/
        └── appimage-builder → .AppImage
            └── packaging/appimage/
```

## Prerequisites

### All Platforms

- Python 3.8 or higher
- pip
- PyInstaller (`pip install pyinstaller`)

### Windows

- Windows 10/11
- [Inno Setup 6.2+](https://jrsoftware.org/isinfo.php)
- Git Bash or PowerShell

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip python3-venv
sudo apt-get install dpkg-dev fakeroot rpm  # For packaging

# Fedora
sudo dnf install python3 python3-pip
sudo dnf install dpkg rpm-build            # For packaging
```

## Detailed Build Instructions

### 1. PyInstaller Executable

The first step packages the Python Flask application into a standalone executable:

```bash
pyinstaller ProjectManager.spec --clean --noconfirm
```

This creates:
- `dist/ProjectManager/` - Directory with executable and all dependencies
- `dist/ProjectManager/ProjectManager` (Linux/macOS)
- `dist/ProjectManager/ProjectManager.exe` (Windows)

#### What Gets Packaged

- Python runtime
- Flask and all dependencies
- Templates (`templates/`)
- Static assets (`static/`)
- Default data files (`projects.json`, `settings.json`)

### 2. Windows Installer

#### Using Inno Setup

The installer provides:
- Installation wizard with custom directory selection
- Desktop shortcut creation (optional)
- Start Menu entries
- File associations (`.pjm` files)
- Auto-start on login option
- Uninstaller with complete cleanup
- Version information for Windows Explorer

#### Build Command

```bash
# On Windows with Inno Setup installed
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

#### Output

- `dist/installer/ProjectManager-2.1.0-Setup.exe`

#### Installer Features

1. **Prerequisites Check**: Verifies if application is already running
2. **Directory Selection**: User can choose installation location
3. **Component Selection**:
   - Desktop shortcut (optional)
   - Quick Launch shortcut (optional)
   - Auto-start on login (optional)
   - File association (optional)
4. **Auto-Close Running Instance**: Prompts to close running app before install
5. **Scheduled Task**: Creates Windows Task Scheduler entry for auto-start
6. **Uninstaller**: Complete removal including scheduled tasks

### 3. Linux Packages

#### Debian/Ubuntu (.deb)

Package structure:
```
packaging/debian/
├── DEBIAN/
│   ├── control      # Package metadata
│   ├── postinst     # Post-installation script
│   └── prerm        # Pre-removal script
└── usr/
    ├── bin/projectmanager         # Wrapper script
    ├── lib/projectmanager/        # Application files
    └── share/
        ├── applications/          # .desktop file
        └── doc/projectmanager/    # Documentation
```

**Build:**
```bash
./build.sh deb
```

**Install:**
```bash
sudo dpkg -i dist/installer/ProjectManager-2.1.0-linux-amd64.deb
sudo apt-get install -f  # Fix dependencies if needed
```

**Uninstall:**
```bash
sudo dpkg -r projectmanager
sudo apt-get purge projectmanager  # Remove config too
```

#### Fedora/RHEL (.rpm)

**Build:**
```bash
./build.sh rpm
```

**Install:**
```bash
sudo rpm -i dist/installer/ProjectManager-2.1.0-linux-amd64.rpm
```

**Uninstall:**
```bash
sudo rpm -e projectmanager
```

#### AppImage (Universal)

AppImage is a universal format that works on most Linux distributions without installation.

**Build:**
```bash
./build.sh appimage
```

**Usage:**
```bash
# Make executable
chmod +x ProjectManager-2.1.0-linux-amd64.AppImage

# Run
./ProjectManager-2.1.0-linux-amd64.AppImage

# Optional: Move to applications directory
mv ProjectManager-2.1.0-linux-amd64.AppImage ~/.local/bin/projectmanager
```

**Benefits:**
- No installation required
- Works on any Linux distribution
- Self-contained with all dependencies
- Can be run from USB drive
- No root privileges needed

## CI/CD with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/build-and-release.yml`) that automatically builds all installers when a new tag is pushed.

### Triggering a Release

```bash
# Tag the release
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

This will:
1. Build Windows executable and installer
2. Build Linux packages (.deb, .rpm, .AppImage)
3. Create a GitHub Release
4. Upload all artifacts
5. Generate checksums

### Manual Trigger

You can also trigger the workflow manually from GitHub Actions with a custom version number.

## Directory Structure After Build

```
dist/
├── installer/
│   ├── ProjectManager-2.1.0-Setup.exe          (Windows)
│   ├── ProjectManager-2.1.0-linux-amd64.deb    (Debian/Ubuntu)
│   ├── ProjectManager-2.1.0-linux-amd64.rpm    (Fedora/RHEL)
│   ├── ProjectManager-2.1.0-linux-amd64.AppImage (Universal)
│   ├── SHA256SUMS
│   └── MD5SUMS
└── ProjectManager/           # Standalone executable (not for distribution)
    ├── ProjectManager        # Main executable
    ├── templates/            # Jinja2 templates
    ├── static/               # CSS/JS assets
    └── ...
```

## Customization

### Changing Version Number

Edit version in these files:
- `version_info.txt` (Windows version info)
- `installer.iss` (Inno Setup)
- `packaging/debian/DEBIAN/control` (Debian package)
- `packaging/rpm/projectmanager.spec` (RPM package)
- `packaging/appimage/appimage-builder.yml` (AppImage)

Or use the build script:
```bash
./build.sh all --version 2.2.0
```

### Adding Icons

Place icon files in `assets/`:
- `icon.ico` - Windows icon (256x256 or multi-resolution)
- `icon.icns` - macOS icon
- `icon.png` - Linux icon (256x256)

### Code Signing

#### Windows

Uncomment the signing section in `installer.iss`:
```pascal
SignTool=signtool
SignedUninstaller=yes
```

Configure signtool with your certificate.

#### Linux

Use GPG signing:
```bash
./build.sh all --sign
```

## Troubleshooting

### Windows

**Issue**: Inno Setup not found
**Solution**: Install Inno Setup and ensure it's in PATH or update path in `installer.iss`

**Issue**: Antivirus flags the installer
**Solution**: Sign the executable with a valid code signing certificate

### Linux

**Issue**: Missing dependencies
**Solution**: Install build prerequisites:
```bash
sudo apt-get install python3-dev build-essential
```

**Issue**: RPM build fails
**Solution**: Ensure rpm-build is installed:
```bash
sudo apt-get install rpm
```

### General

**Issue**: PyInstaller executable won't run
**Solution**: Check that all data files are included in `ProjectManager.spec`

**Issue**: Templates not found
**Solution**: Ensure `--add-data` paths are correct in the spec file

## Security Considerations

1. **Code Signing**: Sign all binaries to prevent tampering
2. **Checksums**: Verify SHA256SUMS before distribution
3. **Sandbox**: The application runs with user permissions (no admin required)
4. **Data Storage**: User data is stored in `~/.local/share/projectmanager/`

## License

The packaging scripts are released under the same license as the Project Manager application (MIT License).

## Support

For issues with the build system:
1. Check the DEBUG_FIX_SUMMARY.md
2. Review build logs in `build/`
3. Open an issue on GitHub with the `packaging` label

---

**Last Updated**: 2025-01-23  
**Version**: 2.1.0
