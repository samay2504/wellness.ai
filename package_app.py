#!/usr/bin/env python3
"""
Complete packaging script for Wellness at Work Desktop Application
Builds both standalone executable and MSIX package
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Package Wellness at Work Desktop Application')
    parser.add_argument('--type', choices=['exe', 'msix', 'both'], default='both',
                       help='Package type to build (default: both)')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build directories before building')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode (console window)')
    return parser.parse_args()

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_modules = ['PyQt6', 'mediapipe', 'cv2', 'numpy', 'requests', 'google.auth']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"❌ Missing required modules: {missing_modules}")
        logger.info("Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All dependencies available")
    return True

def test_application():
    """Test if the application can be imported and runs"""
    logger.info("Testing application...")
    
    try:
        # Add src to path
        src_path = Path('src')
        sys.path.insert(0, str(src_path))
        
        # Test imports
        from desktop_app.main import WellnessAIApp
        logger.info("✅ Application imports successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Application test failed: {e}")
        return False

def build_exe_package(debug=False):
    """Build standalone executable package"""
    logger.info("Building EXE package...")
    
    try:
        from build_desktop_app import main as build_main
        
        # Modify spec file for debug mode
        if debug:
            modify_spec_for_debug()
        
        build_main()
        return True
        
    except Exception as e:
        logger.error(f"❌ EXE build failed: {e}")
        return False

def build_msix_package():
    """Build MSIX package"""
    logger.info("Building MSIX package...")
    
    try:
        from build_msix import main as msix_main
        msix_main()
        return True
        
    except Exception as e:
        logger.error(f"❌ MSIX build failed: {e}")
        return False

def modify_spec_for_debug():
    """Modify spec file for debug mode"""
    spec_file = Path('wellness_app.spec')
    if not spec_file.exists():
        return
    
    content = spec_file.read_text()
    content = content.replace('console=False', 'console=True')
    spec_file.write_text(content)
    logger.info("Modified spec file for debug mode")

def create_release_package():
    """Create a complete release package with documentation"""
    logger.info("Creating release package...")
    
    release_dir = Path('release')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy built packages
    dist_dir = Path('dist')
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file() and item.suffix in ['.exe', '.msix', '.zip']:
                shutil.copy2(item, release_dir)
            elif item.name == 'install.bat':
                shutil.copy2(item, release_dir)
    
    # Create README for release
    readme_content = """# Wellness at Work Desktop Application

## Installation Options

### Option 1: Automatic Installation (Recommended)
1. Download and run `install.bat`
2. Follow the on-screen instructions
3. Application will be installed and shortcuts created

### Option 2: MSIX Package (Windows Store)
1. Download `WellnessAtWork.msix`
2. Double-click to install
3. Note: May require developer mode or certificate trust

### Option 3: Portable Version
1. Download `WellnessAtWork_Portable.zip`
2. Extract to any folder
3. Run `WellnessAtWork.exe` directly

## System Requirements
- Windows 10/11 (64-bit)
- Webcam for eye tracking
- Internet connection for Google OAuth
- 4GB RAM minimum, 8GB recommended

## Features
- Real-time eye tracking and blink detection
- Google OAuth authentication
- Local and cloud data synchronization
- Performance monitoring
- System tray integration

## Troubleshooting
- If antivirus flags the application, add it to exclusions
- For camera permission issues, check Windows privacy settings
- For OAuth issues, ensure internet connection and correct time/date

## Support
For support, please contact: support@wellnessatwork.com
"""
    
    (release_dir / 'README.txt').write_text(readme_content)
    
    # Create version info
    version_info = f"""Wellness at Work Desktop Application
Version: 1.0.0
Build Date: {Path().stat().st_mtime}
Platform: Windows x64

Package Contents:
"""
    
    for item in release_dir.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            version_info += f"- {item.name} ({size_mb:.1f} MB)\n"
    
    (release_dir / 'VERSION.txt').write_text(version_info)
    
    logger.info(f"✅ Release package created in: {release_dir}")

def print_final_summary():
    """Print final build summary"""
    logger.info("\n" + "="*80)
    logger.info("🎉 PACKAGING COMPLETED SUCCESSFULLY!")
    logger.info("="*80)
    
    # Check what was built
    dist_dir = Path('dist')
    release_dir = Path('release')
    
    if dist_dir.exists():
        logger.info("\n📦 Built Packages:")
        for item in dist_dir.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                logger.info(f"  • {item.name} ({size_mb:.1f} MB)")
    
    if release_dir.exists():
        logger.info(f"\n📁 Release package: {release_dir.absolute()}")
        logger.info("  Ready for distribution!")
    
    logger.info("\n🚀 Deployment Instructions:")
    logger.info("  1. Test the executable on a clean Windows machine")
    logger.info("  2. For MSIX: Sign with a trusted certificate for distribution")
    logger.info("  3. Upload to your distribution platform")
    logger.info("  4. Update download links in documentation")
    
    logger.info("\n" + "="*80)

def main():
    """Main packaging workflow"""
    args = parse_arguments()
    
    logger.info("🚀 Starting Wellness at Work packaging process...")
    logger.info(f"Package type: {args.type}")
    logger.info(f"Debug mode: {args.debug}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Test application
    if not test_application():
        sys.exit(1)
    
    # Clean if requested
    if args.clean:
        logger.info("Cleaning build directories...")
        for dir_name in ['build', 'dist', 'msix_build', 'release']:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
    
    # Build packages based on type
    success = True
    
    if args.type in ['exe', 'both']:
        if not build_exe_package(debug=args.debug):
            success = False
    
    if args.type in ['msix', 'both'] and success:
        if not build_msix_package():
            success = False
    
    if success:
        create_release_package()
        print_final_summary()
    else:
        logger.error("❌ Packaging failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
