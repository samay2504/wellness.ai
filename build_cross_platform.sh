#!/bin/bash

# Cross-platform build script for WellnessAI
# Builds for Windows, macOS, and Linux

set -e

echo "🏗️  WellnessAI Cross-Platform Build Script"
echo "=========================================="

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Detect current platform
PLATFORM=$(uname -s)
echo "🖥️  Detected platform: $PLATFORM"

case $PLATFORM in
    "Darwin")
        echo "🍎 Building for macOS..."
        pyinstaller --clean wellness_secure_macos.spec
        echo "✅ macOS build complete: dist/WellnessAI-Secure.app"
        ;;
    "Linux")
        echo "🐧 Building for Linux..."
        pyinstaller --clean wellness_secure_linux.spec
        echo "✅ Linux build complete: dist/WellnessAI-Secure"
        ;;
    "MINGW"*|"CYGWIN"*|"MSYS"*)
        echo "🪟 Building for Windows..."
        pyinstaller --clean wellness_secure.spec
        echo "✅ Windows build complete: dist/WellnessAI-Secure.exe"
        ;;
    *)
        echo "❓ Unknown platform: $PLATFORM"
        echo "Attempting generic Linux build..."
        pyinstaller --clean wellness_secure_linux.spec
        ;;
esac

# Set executable permissions on Unix systems
if [[ "$PLATFORM" != "MINGW"* && "$PLATFORM" != "CYGWIN"* && "$PLATFORM" != "MSYS"* ]]; then
    chmod +x dist/WellnessAI-Secure* 2>/dev/null || true
fi

echo ""
echo "🎉 Build completed successfully!"
echo "📦 Check the dist/ directory for your platform-specific executable"

# Optional: Create a simple installer or package
if command -v zip &> /dev/null; then
    echo "📦 Creating distribution package..."
    cd dist
    case $PLATFORM in
        "Darwin")
            zip -r "WellnessAI-Secure-macOS.zip" WellnessAI-Secure.app/
            echo "✅ macOS package: WellnessAI-Secure-macOS.zip"
            ;;
        "Linux")
            tar -czf "WellnessAI-Secure-linux.tar.gz" WellnessAI-Secure
            echo "✅ Linux package: WellnessAI-Secure-linux.tar.gz"
            ;;
        "MINGW"*|"CYGWIN"*|"MSYS"*)
            zip "WellnessAI-Secure-windows.zip" WellnessAI-Secure.exe
            echo "✅ Windows package: WellnessAI-Secure-windows.zip"
            ;;
    esac
    cd ..
fi

echo ""
echo "🚀 Ready for distribution!"
