#!/usr/bin/env python3
"""
MSIX Packaging script for Wellness at Work Desktop Application
Creates a Windows Store compatible MSIX package
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

def create_msix_structure():
    """Create MSIX package structure"""
    logger.info("Creating MSIX package structure...")
    
    msix_dir = Path('msix_build')
    if msix_dir.exists():
        shutil.rmtree(msix_dir)
    
    msix_dir.mkdir()
    
    # Create required directories
    (msix_dir / 'Assets').mkdir()
    
    # Copy executable and dependencies
    dist_dir = Path('dist/WellnessAtWork_dist')
    if not dist_dir.exists():
        logger.error("❌ Please build the executable first using build_desktop_app.py")
        return False
    
    # Copy all files from dist
    app_dir = msix_dir / 'App'
    shutil.copytree(dist_dir, app_dir)
    
    # Copy manifest
    manifest_src = Path('msix/Package.appxmanifest')
    if manifest_src.exists():
        shutil.copy2(manifest_src, msix_dir / 'Package.appxmanifest')
    else:
        logger.error("❌ Package.appxmanifest not found!")
        return False
    
    # Create placeholder assets (you should replace these with actual images)
    create_placeholder_assets(msix_dir / 'Assets')
    
    logger.info("✅ MSIX structure created")
    return True

def create_placeholder_assets(assets_dir):
    """Create placeholder asset images"""
    logger.info("Creating placeholder assets...")
    
    try:
        from PIL import Image, ImageDraw
        
        # Asset sizes required by MSIX
        assets = {
            'Square44x44Logo.png': (44, 44),
            'Square150x150Logo.png': (150, 150),
            'Wide310x150Logo.png': (310, 150),
            'SplashScreen.png': (620, 300),
            'StoreLogo.png': (50, 50)
        }
        
        for asset_name, size in assets.items():
            img = Image.new('RGB', size, color='#0078D4')  # Microsoft Blue
            draw = ImageDraw.Draw(img)
            
            # Add "WaW" text for Wellness at Work
            text = "WaW"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            draw.text((x, y), text, fill='white')
            
            img.save(assets_dir / asset_name)
            logger.info(f"Created {asset_name}")
    
    except ImportError:
        logger.warning("⚠️ Pillow not installed, creating empty asset files")
        assets = ['Square44x44Logo.png', 'Square150x150Logo.png', 'Wide310x150Logo.png', 'SplashScreen.png', 'StoreLogo.png']
        for asset in assets:
            (assets_dir / asset).touch()

def build_msix_package():
    """Build the MSIX package"""
    logger.info("Building MSIX package...")
    
    msix_dir = Path('msix_build')
    if not msix_dir.exists():
        logger.error("❌ MSIX structure not found!")
        return False
    
    output_file = Path('dist/WellnessAtWork.msix')
    output_file.parent.mkdir(exist_ok=True)
    
    try:
        # Use makeappx.exe from Windows SDK
        makeappx_paths = [
            Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\makeappx.exe"),
            Path(r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x64\makeappx.exe"),
        ]
        
        makeappx_exe = None
        for path in makeappx_paths:
            if path.exists():
                makeappx_exe = path
                break
        
        if not makeappx_exe:
            logger.error("❌ makeappx.exe not found! Please install Windows SDK.")
            logger.info("Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/")
            return False
        
        # Build the MSIX package
        subprocess.run([
            str(makeappx_exe),
            'pack',
            '/d', str(msix_dir),
            '/p', str(output_file)
        ], check=True)
        
        logger.info(f"✅ MSIX package created: {output_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to build MSIX package: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ makeappx.exe not found in PATH")
        return False

def main():
    """Main MSIX packaging workflow"""
    logger.info("🚀 Starting MSIX packaging...")
    
    # Check if executable exists
    if not Path('dist/WellnessAtWork_dist').exists():
        logger.error("❌ Executable not found! Please run build_desktop_app.py first.")
        sys.exit(1)
    
    # Step 1: Create MSIX structure
    if not create_msix_structure():
        sys.exit(1)
    
    # Step 2: Build MSIX package
    if not build_msix_package():
        sys.exit(1)
    
    logger.info("🎉 MSIX packaging completed successfully!")
    logger.info("📦 Package location: dist/WellnessAtWork.msix")
    logger.info("ℹ️ Note: For distribution, the package needs to be signed with a trusted certificate.")

if __name__ == "__main__":
    main()
