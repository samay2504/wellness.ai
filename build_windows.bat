@echo off
REM Cross-platform build script for Windows
REM Builds WellnessAI for Windows platform

echo 🏗️  WellnessAI Windows Build Script
echo ===================================

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build for Windows
echo 🪟 Building for Windows...
pyinstaller --clean wellness_secure.spec

if %errorlevel% equ 0 (
    echo ✅ Windows build complete: dist\WellnessAI-Secure.exe
    
    REM Create distribution package
    if exist "C:\Program Files\7-Zip\7z.exe" (
        echo 📦 Creating distribution package...
        cd dist
        "C:\Program Files\7-Zip\7z.exe" a WellnessAI-Secure-windows.zip WellnessAI-Secure.exe
        echo ✅ Windows package: WellnessAI-Secure-windows.zip
        cd ..
    )
    
    echo.
    echo 🎉 Build completed successfully!
    echo 📦 Check the dist\ directory for your executable
    echo 🚀 Ready for distribution!
) else (
    echo ❌ Build failed!
    exit /b 1
)

pause
