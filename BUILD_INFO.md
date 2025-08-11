# WellnessAI Desktop Application

## Latest Build

The newest WellnessAI desktop application executable has been built with the following features:

### Built Executable
- **File**: `dist/WellnessAI.exe` (standalone)
- **Alternative**: `dist/WellnessAI_dist/WellnessAI.exe` (with dependencies)
- **Icon**: Custom wellness-themed eye icon (`wellness_icon.ico`)
- **Build Date**: August 12, 2025

### Features
- Eye tracking and blink monitoring
- User authentication (local and Google OAuth)
- Real-time performance metrics
- Data synchronization with backend
- Modern PyQt6 interface with custom theme
- Cross-platform compatibility

### Running the Application
```bash
# From the project root
.\dist\WellnessAI.exe

# Or from the dist directory  
cd dist
.\WellnessAI.exe
```

### Build Details
- **Framework**: PyQt6 GUI application
- **Entry Point**: `src/desktop_app/main.py`
- **Build Tool**: PyInstaller with custom spec
- **Dependencies**: Includes MediaPipe, OpenCV, PyQt6, authentication libraries
- **Console**: GUI mode (no console window)

### Icon Design
The application icon features:
- Eye symbol representing the wellness/eye tracking focus
- Blue gradient background
- White highlight for visual appeal
- "W" letter mark for Wellness
- Multiple sizes (16x16 to 256x256)

### Previous Builds Cleaned
All previous build artifacts from the `build/` and old executables have been removed to ensure a clean, current version.
