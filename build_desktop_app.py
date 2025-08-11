#!/usr/bin/env python3
"""
Packaging script for Wellness at Work Desktop Application
Builds standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_packaging_requirements():
    """Install packaging dependencies"""
    logger.info("Installing packaging requirements...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'packaging_requirements.txt'
        ], check=True)
        logger.info("✅ Packaging requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install packaging requirements: {e}")
        return False
    return True

def clean_build_dirs():
    """Clean previous build directories"""
    logger.info("Cleaning previous build directories...")
    dirs_to_clean = ['build', 'dist', '__pycache__', 'WellnessAtWork_dist']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            logger.info(f"Removed {dir_name}")
    
    # Clean __pycache__ in src directory
    src_path = Path('src')
    for pycache in src_path.rglob('__pycache__'):
        shutil.rmtree(pycache)
        logger.info(f"Removed {pycache}")

def build_executable():
    """Build the executable using PyInstaller"""
    logger.info("Building executable with PyInstaller...")
    
    try:
        # Run PyInstaller with our spec file
        subprocess.run([
            sys.executable, '-m', 'PyInstaller', 
            '--clean',
            'wellness_app.spec'
        ], check=True)
        
        logger.info("✅ Executable built successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ PyInstaller build failed: {e}")
        return False

def create_data_structure():
    """Create necessary data directories in the distribution"""
    logger.info("Creating data structure...")
    
    dist_path = Path('dist')
    if not dist_path.exists():
        logger.error("❌ Distribution directory not found!")
        return False
    
    # Find the executable directory
    exe_dirs = [d for d in dist_path.iterdir() if d.is_dir()]
    if not exe_dirs:
        logger.error("❌ No executable directory found in dist!")
        return False
    
    exe_dir = exe_dirs[0]  # Should be WellnessAtWork_dist
    
    # Create data directories
    data_dirs = ['data', 'data/eye_tracking', 'logs']
    for data_dir in data_dirs:
        (exe_dir / data_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created {data_dir} directory")
    
    # Create empty database file
    db_file = exe_dir / 'data' / 'local.db'
    if not db_file.exists():
        db_file.touch()
        logger.info("Created empty local.db file")
    
    return True

def create_installer_script():
    """Create a simple installer script"""
    logger.info("Creating installer script...")
    
    installer_content = '''@echo off
echo Installing Wellness at Work Desktop Application...
echo.

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\\WellnessAtWork
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying application files...
xcopy /E /I /Y "WellnessAtWork_dist\\*" "%INSTALL_DIR%\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\Wellness at Work.lnk
powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%INSTALL_DIR%\\WellnessAtWork.exe'; $s.Save()"

REM Create start menu entry
set STARTMENU_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Wellness at Work
if not exist "%STARTMENU_DIR%" mkdir "%STARTMENU_DIR%"
set STARTMENU_SHORTCUT=%STARTMENU_DIR%\\Wellness at Work.lnk
powershell "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTMENU_SHORTCUT%'); $s.TargetPath = '%INSTALL_DIR%\\WellnessAtWork.exe'; $s.Save()"

echo.
echo ✅ Installation completed successfully!
echo Application installed to: %INSTALL_DIR%
echo Desktop shortcut created
echo Start menu entry created
echo.
pause
'''
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_content)
    
    logger.info("✅ Installer script created: dist/install.bat")

def create_portable_package():
    """Create a portable ZIP package"""
    logger.info("Creating portable package...")
    
    try:
        import zipfile
        
        with zipfile.ZipFile('dist/WellnessAtWork_Portable.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            dist_dir = Path('dist/WellnessAtWork_dist')
            if dist_dir.exists():
                for file_path in dist_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(dist_dir.parent)
                        zipf.write(file_path, arcname)
                
                logger.info("✅ Portable ZIP package created: dist/WellnessAtWork_Portable.zip")
                return True
            else:
                logger.error("❌ Distribution directory not found!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Failed to create portable package: {e}")
        return False

def print_build_summary():
    """Print build summary"""
    logger.info("\n" + "="*60)
    logger.info("🎉 BUILD COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    
    dist_path = Path('dist')
    if dist_path.exists():
        logger.info("\nGenerated files:")
        for item in dist_path.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                logger.info(f"  📦 {item.name} ({size_mb:.1f} MB)")
            elif item.is_dir():
                logger.info(f"  📁 {item.name}/")
    
    logger.info("\nInstallation options:")
    logger.info("  1. Run 'dist/install.bat' for automatic installation")
    logger.info("  2. Extract 'dist/WellnessAtWork_Portable.zip' for portable use")
    logger.info("  3. Copy 'dist/WellnessAtWork_dist/' folder manually")
    
    logger.info("\n" + "="*60)

def main():
    """Main packaging workflow"""
    logger.info("🚀 Starting Wellness at Work Desktop App packaging...")
    
    # Step 1: Install packaging requirements
    if not install_packaging_requirements():
        sys.exit(1)
    
    # Step 2: Clean build directories
    clean_build_dirs()
    
    # Step 3: Build executable
    if not build_executable():
        sys.exit(1)
    
    # Step 4: Create data structure
    if not create_data_structure():
        sys.exit(1)
    
    # Step 5: Create installer script
    create_installer_script()
    
    # Step 6: Create portable package
    create_portable_package()
    
    # Step 7: Print summary
    print_build_summary()

if __name__ == "__main__":
    main()
