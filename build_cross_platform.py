#!/usr/bin/env python3
"""
Cross-platform build script for WellnessAI application
Supports Windows (.exe), macOS (.app), and Linux (binary)
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrossPlatformBuilder:
    """Build WellnessAI application for multiple platforms"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.src_dir = self.root_dir / "src"
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.current_os = platform.system()
        
    def clean_build_directories(self):
        """Clean previous build artifacts"""
        logger.info("Cleaning build directories...")
        for directory in [self.dist_dir, self.build_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                logger.info(f"Removed {directory}")
        
    def install_dependencies(self):
        """Install required dependencies"""
        logger.info("Installing dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "pyinstaller", "auto-py-to-exe"
        ], check=True)
        
    def create_windows_spec(self):
        """Create Windows-specific PyInstaller spec"""
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src to Python path
src_path = Path('src').resolve()
sys.path.insert(0, str(src_path))

a = Analysis(
    ['src/desktop_app/main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('configs', 'configs'),
        ('data', 'data'),
        ('src/desktop_app/ui.py', 'desktop_app'),
        ('src/desktop_app/auth.py', 'desktop_app'),
        ('src/desktop_app/metrics.py', 'desktop_app'),
        ('src/desktop_app/sync.py', 'desktop_app'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets', 
        'PyQt6.QtGui',
        'mediapipe',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'psutil',
        'requests',
        'keyring',
        'keyring.backends',
        'keyring.backends.Windows',
        'google.auth',
        'google.oauth2',
        'google_auth_oauthlib',
        'flask',
        'sqlalchemy',
        'werkzeug',
        'bcrypt',
        'jwt',
        'desktop_app.auth',
        'desktop_app.ui',
        'desktop_app.metrics',
        'desktop_app.sync',
        'desktop_app.eye_tracker',
        'desktop_app.eye_tracker_ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
'''
        spec_path = self.root_dir / "wellness_windows.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path
        
    def create_macos_spec(self):
        """Create macOS-specific PyInstaller spec"""
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src to Python path
src_path = Path('src').resolve()
sys.path.insert(0, str(src_path))

a = Analysis(
    ['src/desktop_app/main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('configs', 'configs'),
        ('data', 'data'),
        ('src/desktop_app/ui.py', 'desktop_app'),
        ('src/desktop_app/auth.py', 'desktop_app'),
        ('src/desktop_app/metrics.py', 'desktop_app'),
        ('src/desktop_app/sync.py', 'desktop_app'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets', 
        'PyQt6.QtGui',
        'mediapipe',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'psutil',
        'requests',
        'keyring',
        'keyring.backends',
        'keyring.backends.macOS',
        'google.auth',
        'google.oauth2',
        'google_auth_oauthlib',
        'flask',
        'sqlalchemy',
        'werkzeug',
        'bcrypt',
        'jwt',
        'desktop_app.auth',
        'desktop_app.ui',
        'desktop_app.metrics',
        'desktop_app.sync',
        'desktop_app.eye_tracker',
        'desktop_app.eye_tracker_ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WellnessAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WellnessAI',
)

app = BUNDLE(
    coll,
    name='WellnessAI.app',
    icon='assets/icon.icns',
    bundle_identifier='com.wellnessai.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'WellnessAI Document',
                'CFBundleTypeRole': 'Editor',
                'LSItemContentTypes': ['public.text'],
            }
        ]
    },
)
'''
        spec_path = self.root_dir / "wellness_macos.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path
        
    def create_linux_spec(self):
        """Create Linux-specific PyInstaller spec"""
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src to Python path
src_path = Path('src').resolve()
sys.path.insert(0, str(src_path))

a = Analysis(
    ['src/desktop_app/main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('configs', 'configs'),
        ('data', 'data'),
        ('src/desktop_app/ui.py', 'desktop_app'),
        ('src/desktop_app/auth.py', 'desktop_app'),
        ('src/desktop_app/metrics.py', 'desktop_app'),
        ('src/desktop_app/sync.py', 'desktop_app'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets', 
        'PyQt6.QtGui',
        'mediapipe',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'psutil',
        'requests',
        'keyring',
        'keyring.backends',
        'keyring.backends.SecretService',
        'google.auth',
        'google.oauth2',
        'google_auth_oauthlib',
        'flask',
        'sqlalchemy',
        'werkzeug',
        'bcrypt',
        'jwt',
        'desktop_app.auth',
        'desktop_app.ui',
        'desktop_app.metrics',
        'desktop_app.sync',
        'desktop_app.eye_tracker',
        'desktop_app.eye_tracker_ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='wellness-ai',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        spec_path = self.root_dir / "wellness_linux.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        return spec_path
        
    def build_windows(self):
        """Build Windows executable"""
        logger.info("Building Windows executable...")
        spec_path = self.create_windows_spec()
        
        subprocess.run([
            "pyinstaller", 
            "--clean",
            str(spec_path)
        ], check=True, cwd=self.root_dir)
        
        logger.info("Windows build completed successfully!")
        
    def build_macos(self):
        """Build macOS application"""
        logger.info("Building macOS application...")
        spec_path = self.create_macos_spec()
        
        subprocess.run([
            "pyinstaller", 
            "--clean",
            str(spec_path)
        ], check=True, cwd=self.root_dir)
        
        logger.info("macOS build completed successfully!")
        
    def build_linux(self):
        """Build Linux binary"""
        logger.info("Building Linux binary...")
        spec_path = self.create_linux_spec()
        
        subprocess.run([
            "pyinstaller", 
            "--clean",
            str(spec_path)
        ], check=True, cwd=self.root_dir)
        
        logger.info("Linux build completed successfully!")
        
    def build_current_platform(self):
        """Build for current platform"""
        self.clean_build_directories()
        self.install_dependencies()
        
        if self.current_os == "Windows":
            self.build_windows()
        elif self.current_os == "Darwin":  # macOS
            self.build_macos()
        elif self.current_os == "Linux":
            self.build_linux()
        else:
            logger.error(f"Unsupported platform: {self.current_os}")
            sys.exit(1)
            
    def build_all_platforms(self):
        """Build for all supported platforms (requires Docker or VMs)"""
        logger.info("Cross-platform build requires platform-specific environments")
        logger.info("Building for current platform only")
        self.build_current_platform()


def main():
    """Main build function"""
    builder = CrossPlatformBuilder()
    
    if len(sys.argv) > 1:
        platform_arg = sys.argv[1].lower()
        if platform_arg == "windows":
            builder.build_windows()
        elif platform_arg == "macos":
            builder.build_macos()
        elif platform_arg == "linux":
            builder.build_linux()
        elif platform_arg == "all":
            builder.build_all_platforms()
        else:
            logger.error(f"Unknown platform: {platform_arg}")
            sys.exit(1)
    else:
        builder.build_current_platform()


if __name__ == "__main__":
    main()
