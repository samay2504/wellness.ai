# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory
project_root = Path.cwd()
src_path = project_root / 'src'

# Collect MediaPipe data files
mediapipe_datas = []
try:
    mediapipe_datas = collect_data_files('mediapipe')
except ImportError:
    pass

# Define data files and directories to include
datas = [
    # Configuration files
    (str(project_root / 'configs'), 'configs'),
    
    # Backend database directory (create if not exists)
    (str(project_root / 'backend' / 'instance'), 'backend/instance'),
    
    # Data directory
    (str(project_root / 'data'), 'data'),
    
    # Desktop app assets including icon
    (str(src_path / 'desktop_app' / 'assets'), 'desktop_app/assets'),
    
    # Include any .env files
    (str(src_path / 'desktop_app'), 'desktop_app'),
]

# Add MediaPipe data files
datas.extend(mediapipe_datas)

# Comprehensive hidden imports for the updated application
hiddenimports = [
    # Core Python modules
    'sqlite3',
    'json',
    'pathlib',
    'threading',
    'logging',
    'uuid',
    'dataclasses',
    'typing',
    'platform',
    'os',
    'sys',
    'time',
    'datetime',
    
    # Computer Vision and AI
    'mediapipe',
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'Pillow',
    
    # GUI Framework
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    'PyQt6.QtNetwork',
    'PyQt6.sip',
    
    # Authentication and Security
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'redis',
    'PyJWT',
    'passlib',
    'passlib.hash',
    
    # Network and HTTP
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    
    # System Monitoring
    'psutil',
    
    # Configuration and Data
    'yaml',
    'python-dotenv',
    'boto3',
    'botocore',
    
    # Application modules
    'desktop_app',
    'desktop_app.auth',
    'desktop_app.ui',
    'desktop_app.auth_service',
    'desktop_app.data_storage',
    'desktop_app.themes',
    'desktop_app.themes.theme',
    'desktop_app.metrics',
    'desktop_app.sync',
    'desktop_app.eye_tracker',
    'desktop_app.eye_tracker_ui',
    'desktop_app.blink_tracker',
    'desktop_app.email_auth_dialog',
    
    # Additional MediaPipe components
    'mediapipe.python',
    'mediapipe.python.solutions',
    'mediapipe.framework.formats',
]

# Collect all submodules for critical packages
try:
    hiddenimports.extend(collect_submodules('mediapipe'))
except ImportError:
    pass

try:
    hiddenimports.extend(collect_submodules('google.auth'))
except ImportError:
    pass

# Exclude unnecessary modules to reduce executable size
excludes = [
    'tkinter',
    'IPython',
    'pandas',
    'scipy',
    'sympy',
    'pytest',
    'sphinx',
    'jupyter',
    'notebook',
    'tornado',
    'zmq',
    'pygame',
    'selenium',
]

# Analysis configuration
a = Analysis(
    ['src/desktop_app/main.py'],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# Remove duplicate files and optimize
pyz = PYZ(a.pure, a.zipped_data)

# Create the executable with enhanced configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WellnessAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
        icon='src/desktop_app/assets/wellness_icon.ico',  # Use our custom icon
    version=None,  # Add version info if available
)

# Create distribution folder for easy deployment
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WellnessAI_dist',
)
