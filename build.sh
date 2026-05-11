#!/bin/bash
#
# Unified Build Script for Project Manager
# Builds standalone executables and installers for Windows and Linux
#
# Usage:
#   ./build.sh [command] [options]
#
# Commands:
#   all         - Build everything (default)
#   windows     - Build Windows executable and installer
#   linux       - Build Linux packages (deb, rpm, AppImage)
#   deb         - Build Debian package only
#   rpm         - Build RPM package only
#   appimage    - Build AppImage only
#   clean       - Clean build artifacts
#
# Options:
#   --version VERSION    - Set version (default: read from version.py)
#   --sign               - Sign binaries (requires certificates)
#   --upload             - Upload to GitHub releases (requires GH CLI)
#
# Examples:
#   ./build.sh all
#   ./build.sh windows
#   ./build.sh deb --sign
#

set -e

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Read version from version.py
if [ -f "version.py" ]; then
    APP_VERSION=$(python3 -c "from version import __version__; print(__version__)" 2>/dev/null || echo "2.1.0")
    APP_NAME=$(python3 -c "from version import __app_name__; print(__app_name__.replace(' ', ''))" 2>/dev/null || echo "ProjectManager")
else
    APP_VERSION="2.1.0"
    APP_NAME="ProjectManager"
fi

APP_AUTHOR="Rehar.Lab"
APP_DESCRIPTION="Production-ready project manager"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
COMMAND="${1:-all}"
shift || true

SIGN_BINARIES=false
UPLOAD_RELEASE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            APP_VERSION="$2"
            shift 2
            ;;
        --sign)
            SIGN_BINARIES=true
            shift
            ;;
        --upload)
            UPLOAD_RELEASE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Building $APP_NAME v$APP_VERSION"
log_info "Project root: $PROJECT_ROOT"

# Create necessary directories
mkdir -p dist dist/installer assets

# Function: Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        exit 1
    fi
    
    # Check PyInstaller
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        log_warn "PyInstaller not found. Installing..."
        pip3 install pyinstaller
    fi
    
    log_success "Dependencies check passed"
}

# Function: Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    pip3 install -r requirements.txt -q
    log_success "Python dependencies installed"
}

# Function: Update version in all files
update_version() {
    log_info "Updating version to $APP_VERSION in all files..."
    
    # Update version.py
    sed -i.bak "s/__version__ = ".*"/__version__ = \"$APP_VERSION\"/" version.py
    rm -f version.py.bak
    
    # Update version_info.txt (Windows)
    cat > version_info.txt << EOF
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($(echo $APP_VERSION | tr '.' ','), 0),
    prodvers=($(echo $APP_VERSION | tr '.' ','), 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Rehar.Lab'),
        StringStruct('FileDescription', 'Project Control Dashboard'),
        StringStruct('FileVersion', '$APP_VERSION.0'),
        StringStruct('InternalName', '$APP_NAME'),
        StringStruct('LegalCopyright', 'Copyright (C) $(date +%Y) Rehar.Lab'),
        StringStruct('OriginalFilename', '$APP_NAME.exe'),
        StringStruct('ProductName', 'Project Manager'),
        StringStruct('ProductVersion', '$APP_VERSION.0')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
EOF
    
    # Update Inno Setup script
    sed -i.bak "s/#define MyAppVersion \".*\"/#define MyAppVersion \"$APP_VERSION\"/" installer.iss
    rm -f installer.iss.bak
    
    # Update Debian control
    sed -i.bak "s/Version: .*/Version: $APP_VERSION/" packaging/debian/DEBIAN/control
    rm -f packaging/debian/DEBIAN/control.bak
    
    # Update RPM spec
    sed -i.bak "s/Version:        .*/Version:        $APP_VERSION/" packaging/rpm/projectmanager.spec
    rm -f packaging/rpm/projectmanager.spec.bak
    
    log_success "Version updated to $APP_VERSION"
}

# Function: Build executable with PyInstaller
build_executable() {
    log_info "Building executable with PyInstaller..."
    
    # Clean previous builds
    rm -rf build dist/*.spec dist/ProjectManager 2>/dev/null || true
    
    # Build
    python3 -m PyInstaller ProjectManager.spec --clean --noconfirm
    
    log_success "Executable built successfully"
}

# Function: Build Windows installer
build_windows() {
    log_info "Building Windows installer..."
    
    if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" && "$OSTYPE" != "win32" ]]; then
        log_warn "Not on Windows. Windows installer can only be built on Windows."
        log_warn "Skipping Windows build."
        return
    fi
    
    # Check for Inno Setup
    if [[ ! -f "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ]]; then
        log_error "Inno Setup not found. Please install Inno Setup 6."
        exit 1
    fi
    
    # Build installer
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    
    log_success "Windows installer built: dist/installer/${APP_NAME}-${APP_VERSION}-Setup.exe"
}

# Function: Build Debian package
build_deb() {
    log_info "Building Debian package..."
    
    # Check for dpkg-deb
    if ! command -v dpkg-deb &> /dev/null; then
        log_error "dpkg-deb not found. Please install dpkg-dev."
        exit 1
    fi
    
    # Copy binary to package
    cp -r dist/ProjectManager/* packaging/debian/usr/lib/projectmanager/
    
    # Set permissions
    chmod +x packaging/debian/usr/bin/projectmanager
    chmod +x packaging/debian/DEBIAN/postinst
    chmod +x packaging/debian/DEBIAN/prerm
    
    # Build package
    dpkg-deb --build packaging/debian dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.deb
    
    log_success "Debian package built: dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.deb"
}

# Function: Build RPM package
build_rpm() {
    log_info "Building RPM package..."
    
    # Check for rpmbuild
    if ! command -v rpmbuild &> /dev/null; then
        log_error "rpmbuild not found. Please install rpm-build."
        exit 1
    fi
    
    # Create RPM build structure
    mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    
    # Build RPM using the spec file directly
    # The spec uses %%{sourcedir} which points to the project root
    rpmbuild -bb packaging/rpm/projectmanager.spec \
        --define "_sourcedir $PROJECT_ROOT" \
        --define "_version $APP_VERSION"
    
    # Copy to dist
    cp ~/rpmbuild/RPMS/x86_64/*.rpm dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.rpm
    
    log_success "RPM package built: dist/installer/${APP_NAME}-${APP_VERSION}-linux-amd64.rpm"
}

# Function: Build AppImage
build_appimage() {
    log_info "Building AppImage using appimagetool..."
    
    # Check for required files
    if [ ! -d "dist/ProjectManager" ]; then
        log_error "dist/ProjectManager not found. Run PyInstaller first."
        exit 1
    fi
    
    # Use the dedicated AppImage build script
    chmod +x packaging/appimage/build-appimage.sh
    ./packaging/appimage/build-appimage.sh
    
    log_success "AppImage built!"
}

# Function: Build all Linux packages
build_linux() {
    log_info "Building all Linux packages..."
    build_deb
    build_rpm
    build_appimage
}

# Function: Sign binaries (placeholder for actual signing)
sign_binaries() {
    if [[ "$SIGN_BINARIES" == true ]]; then
        log_info "Signing binaries..."
        
        # Windows signing (requires signtool and certificate)
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
            if command -v signtool &> /dev/null; then
                for file in dist/installer/*.exe; do
                    signtool sign /f "$CERTIFICATE_PATH" /p "$CERTIFICATE_PASSWORD" /t http://timestamp.digicert.com "$file"
                done
            fi
        fi
        
        # Linux signing (GPG)
        if command -v gpg &> /dev/null; then
            for file in dist/installer/*.{deb,rpm,AppImage}; do
                if [[ -f "$file" ]]; then
                    gpg --armor --detach-sign "$file"
                fi
            done
        fi
        
        log_success "Binaries signed"
    fi
}

# Function: Generate checksums
generate_checksums() {
    log_info "Generating checksums..."
    
    cd dist/installer
    
    # SHA256
    sha256sum * > SHA256SUMS
    
    # MD5
    md5sum * > MD5SUMS
    
    cd "$PROJECT_ROOT"
    
    log_success "Checksums generated"
}

# Function: Upload to GitHub releases
upload_release() {
    if [[ "$UPLOAD_RELEASE" == true ]]; then
        log_info "Uploading to GitHub releases..."
        
        if ! command -v gh &> /dev/null; then
            log_error "GitHub CLI (gh) not found"
            exit 1
        fi
        
        # Create release if it doesn't exist
        if ! gh release view "v$APP_VERSION" &> /dev/null; then
            gh release create "v$APP_VERSION" \
                --title "Release v$APP_VERSION" \
                --notes "Project Manager v$APP_VERSION"
        fi
        
        # Upload assets
        gh release upload "v$APP_VERSION" dist/installer/*
        
        log_success "Release uploaded"
    fi
}

# Function: Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."
    
    rm -rf build dist __pycache__
    rm -rf AppDir
    rm -rf packaging/debian/usr/lib/projectmanager/*
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.bak" -delete 2>/dev/null || true
    
    log_success "Clean complete"
}

# Function: Print help
print_help() {
    cat << 'EOF'
Unified Build Script for Project Manager

Usage:
  ./build.sh [command] [options]

Commands:
  all         - Build everything (default)
  windows     - Build Windows executable and installer
  linux       - Build all Linux packages (deb, rpm, AppImage)
  deb         - Build Debian package only
  rpm         - Build RPM package only
  appimage    - Build AppImage only
  clean       - Clean build artifacts
  help        - Show this help message

Options:
  --version VERSION    - Set version (default: read from version.py)
  --sign               - Sign binaries (requires certificates)
  --upload             - Upload to GitHub releases (requires GH CLI)

Examples:
  ./build.sh all
  ./build.sh windows
  ./build.sh deb --sign
  ./build.sh clean

Requirements:
  - Python 3.8+
  - pip
  - PyInstaller
  - Windows: Inno Setup 6
  - Linux: dpkg-dev (for .deb), rpm-build (for .rpm)
EOF
}

# Main execution
case "$COMMAND" in
    help|--help|-h)
        print_help
        exit 0
        ;;
    clean)
        clean
        exit 0
        ;;
    all)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_windows
        build_linux
        sign_binaries
        generate_checksums
        upload_release
        log_success "Build complete! Artifacts in dist/installer/"
        ;;
    windows)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_windows
        sign_binaries
        generate_checksums
        log_success "Windows build complete!"
        ;;
    linux)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_linux
        sign_binaries
        generate_checksums
        log_success "Linux build complete!"
        ;;
    deb)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_deb
        sign_binaries
        log_success "Debian package built!"
        ;;
    rpm)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_rpm
        sign_binaries
        log_success "RPM package built!"
        ;;
    appimage)
        check_dependencies
        install_python_deps
        update_version
        build_executable
        build_appimage
        sign_binaries
        log_success "AppImage built!"
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        print_help
        exit 1
        ;;
esac
