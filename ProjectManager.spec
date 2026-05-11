# -*- mode: python ; coding: utf-8 -*-
"""
Project Manager - PyInstaller Spec File
Creates standalone executable from Flask application
"""

import sys
import os
from pathlib import Path

# Get project root
project_root = Path(SPECDIR).parent if hasattr(SPECDIR, 'parent') else Path.cwd()

# Import version from version.py
version_file = project_root / 'version.py'
if version_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("version", version_file)
    version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version_module)
    APP_VERSION = version_module.__version__
    APP_AUTHOR = version_module.__author__
    APP_NAME = version_module.__app_name__.replace(' ', '')
    APP_DESCRIPTION = version_module.__description__
else:
    # Fallback values
    APP_NAME = 'ProjectManager'
    APP_VERSION = '2.1.0'
    APP_AUTHOR = 'Rehar.Lab'
    APP_DESCRIPTION = 'Production-ready project manager with multi-service support'

# Determine platform
is_windows = sys.platform.startswith('win')
is_linux = sys.platform.startswith('linux')
is_macos = sys.platform == 'darwin'

# Data files to include
data_files = [
    # Templates
    (str(project_root / 'templates'), 'templates'),
    # Static assets
    (str(project_root / 'static'), 'static'),
    # Data files (will be created on first run, but include defaults)
    (str(project_root / 'projects.json'), '.'),
    (str(project_root / 'settings.json'), '.'),
    # Version file
    (str(project_root / 'version.py'), '.'),
]

# Binaries (if any native libs need to be included)
binaries = []

# Hidden imports for Flask
hiddenimports = [
    'flask',
    'jinja2',
    'markupsafe',
    'werkzeug',
    'psutil',
    'services',
    'services.project_service',
    'services.process_service',
    'services.system_service',
    'services.health_monitor',
    'version',
    'webbrowser',
    'threading',
    'tkinter',
    'tkinter.messagebox',
]

# Excluded modules to reduce size
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'unittest',
    'pydoc',
    'email',
    'http.server',
    'socketserver',
    'sqlite3.test',
    'pdb',
    'doctest',
]

# Collect all Flask internals to ensure nothing is missed
collect_all = [
    'flask',
    'jinja2',
    'werkzeug',
    'markupsafe',
]

a = Analysis(
    [str(project_root / 'app.py')],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=data_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Collect all modules to ensure complete bundling
for module in collect_all:
    try:
        import importlib
        mod = importlib.import_module(module)
        mod_path = Path(mod.__file__).parent
        if mod_path.exists():
            a.datas += Tree(str(mod_path), prefix=module)
    except Exception:
        pass

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Icon paths
if is_windows:
    icon_file = str(project_root / 'assets' / 'icon.ico')
elif is_macos:
    icon_file = str(project_root / 'assets' / 'icon.icns')
else:
    icon_file = str(project_root / 'assets' / 'icon.png')

# Check if icon exists, if not use None
icon = icon_file if Path(icon_file).exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    version=str(project_root / 'version_info.txt') if (project_root / 'version_info.txt').exists() else None,
    # Windows-specific
    uac_admin=False,
)

# macOS app bundle (only on macOS)
if is_macos:
    app = BUNDLE(
        exe,
        name=f'{APP_NAME}.app',
        icon=icon,
        bundle_identifier='com.reharlab.projectmanager',
        version=APP_VERSION,
        info_plist={
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': 'True',
        },
    )
