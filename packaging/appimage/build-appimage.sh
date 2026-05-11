#!/bin/bash
#
# AppImage Build Script using appimagetool
# Direct approach - more reliable than appimage-builder
#

set -e

APP_NAME="ProjectManager"
APP_VERSION="2.1.0"
APPDIR="AppDir"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO] Building AppImage for ${APP_NAME} v${APP_VERSION}${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# Check for PyInstaller build
if [ ! -d "dist/ProjectManager" ]; then
    echo -e "${RED}[ERROR] dist/ProjectManager not found. Run PyInstaller first.${NC}"
    echo "Run: pyinstaller ProjectManager.spec"
    exit 1
fi

# Download appimagetool if not present
APPIMAGETOOL="/tmp/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo -e "${BLUE}[INFO] Downloading appimagetool...${NC}"
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
    chmod +x "$APPIMAGETOOL"
fi

# Clean and create AppDir
echo -e "${BLUE}[INFO] Preparing AppDir...${NC}"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller build to AppDir
echo -e "${BLUE}[INFO] Copying application files...${NC}"
cp -r dist/ProjectManager/* "$APPDIR/usr/bin/"

# Create AppRun script
echo -e "${BLUE}[INFO] Creating AppRun...${NC}"
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash

# AppRun script for Project Manager AppImage
# This script is the entry point for the AppImage

# Get the directory where the AppImage is located
APPDIR="$(dirname "$(readlink -f "$0")")"

# Set up user data directories
export PROJECT_MANAGER_HOME="${HOME}/.local/share/projectmanager"
export PROJECT_MANAGER_CONFIG="${HOME}/.config/projectmanager"

# Create directories if they don't exist
mkdir -p "$PROJECT_MANAGER_HOME"
mkdir -p "$PROJECT_MANAGER_CONFIG"

# Initialize default files if needed
if [ ! -f "$PROJECT_MANAGER_HOME/projects.json" ]; then
    echo '[]' > "$PROJECT_MANAGER_HOME/projects.json"
fi

if [ ! -f "$PROJECT_MANAGER_CONFIG/settings.json" ]; then
    cat > "$PROJECT_MANAGER_CONFIG/settings.json" << 'EOF'
{
    "theme": "dark",
    "refresh_interval": 5,
    "auto_start_projects": false,
    "show_notifications": true,
    "minimize_logging": false
}
EOF
fi

# Run the application
exec "$APPDIR/usr/bin/ProjectManager" "$@"
APPRUN

chmod +x "$APPDIR/AppRun"

# Create .desktop file
echo -e "${BLUE}[INFO] Creating desktop file...${NC}"
cat > "$APPDIR/usr/share/applications/projectmanager.desktop" << 'DESKTOP'
[Desktop Entry]
Name=Project Manager
Comment=Production-ready project manager with multi-service support
Exec=AppRun
Icon=projectmanager
Type=Application
Categories=System;Monitor;Development;
Terminal=false
StartupNotify=true
StartupWMClass=ProjectManager
DESKTOP

# Also create in AppDir root
cp "$APPDIR/usr/share/applications/projectmanager.desktop" "$APPDIR/projectmanager.desktop"

# Copy or create icon
if [ -f "assets/icon.png" ]; then
    cp "assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/projectmanager.png"
    cp "assets/icon.png" "$APPDIR/projectmanager.png"
else
    # Create a simple placeholder icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 256x256 xc:#D97941 -pointsize 30 -fill white -gravity center -annotate +0+0 "PM" "$APPDIR/projectmanager.png"
        cp "$APPDIR/projectmanager.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/projectmanager.png"
    else
        touch "$APPDIR/projectmanager.png"
        touch "$APPDIR/usr/share/icons/hicolor/256x256/apps/projectmanager.png"
    fi
fi

# Create icon symlink in AppDir root
ln -sf "usr/share/icons/hicolor/256x256/apps/projectmanager.png" "$APPDIR/.DirIcon"

# Build AppImage
echo -e "${BLUE}[INFO] Building AppImage...${NC}"
mkdir -p dist/installer

# Use appimagetool to create the AppImage
"$APPIMAGETOOL" "$APPDIR" "dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.AppImage" --appimage-extract-and-run 2>&1 | grep -v "WARNING:" || true

# Check if AppImage was created
if [ -f "dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.AppImage" ]; then
    chmod +x "dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.AppImage"
    echo -e "${GREEN}[SUCCESS] AppImage created: dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.AppImage${NC}"
    ls -lh "dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.AppImage"
else
    echo -e "${RED}[ERROR] Failed to create AppImage${NC}"
    exit 1
fi

# Cleanup
rm -rf "$APPDIR"

echo -e "${GREEN}[SUCCESS] AppImage build complete!${NC}"
