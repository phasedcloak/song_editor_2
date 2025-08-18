# Song Editor 2 - Build Instructions

This document provides comprehensive build instructions for Song Editor 2 across all supported platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [macOS Build](#macos-build)
- [Windows Build](#windows-build)
- [iOS Build](#ios-build)
- [Android Build](#android-build)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### General Requirements
- Python 3.8 or higher
- Git
- pip (Python package manager)

### Platform-Specific Requirements

#### macOS
- macOS 10.14 or higher
- Xcode Command Line Tools
- Homebrew (recommended)

#### Windows
- Windows 10 or higher
- Visual Studio Build Tools
- NSIS (for installer creation)

#### iOS
- macOS with Xcode
- Apple Developer Account (for App Store distribution)
- iOS deployment tools

#### Android
- Android Studio
- Android SDK and NDK
- Java JDK 8 or 11

## macOS Build

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd Song_Editor_2

# Install dependencies
pip install -r requirements.txt

# Run the build script
python build_macos.py
```

### Manual Build Process

1. **Install Dependencies:**
```bash
pip install pyinstaller pyinstaller-hooks-contrib
```

2. **Create Application Bundle:**
```bash
pyinstaller --onefile --windowed --name "Song Editor 2" song_editor/app.py
```

3. **Create DMG Installer (Optional):**
```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Song Editor 2" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "Song Editor 2.app" 175 120 \
  --hide-extension "Song Editor 2.app" \
  --app-drop-link 425 120 \
  "Song_Editor_2_v2.0.0_macOS.dmg" \
  "dist/"
```

### Code Signing (Recommended)
```bash
# Sign the application
codesign --force --deep --sign "Developer ID Application: Your Name" "dist/Song Editor 2.app"

# Verify signature
codesign --verify --deep --strict "dist/Song Editor 2.app"
```

## Windows Build

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd Song_Editor_2

# Install dependencies
pip install -r requirements.txt

# Run the build script
python build_windows.py
```

### Manual Build Process

1. **Install Dependencies:**
```bash
pip install pyinstaller pyinstaller-hooks-contrib
```

2. **Create Executable:**
```bash
pyinstaller --onefile --windowed --name "Song Editor 2" song_editor/app.py
```

3. **Create NSIS Installer (Optional):**
```bash
# Install NSIS
# Download from: https://nsis.sourceforge.io/Download

# Run NSIS compiler
makensis installer.nsi
```

### Windows-Specific Considerations

- **Antivirus Software:** Some antivirus software may flag PyInstaller-generated executables. You may need to add exceptions.
- **Windows Defender:** May require adding the executable to the exclusion list during development.
- **Dependencies:** Ensure all Visual C++ redistributables are installed on target systems.

## iOS Build

### Overview
Building for iOS requires adapting the PySide6-based application for mobile platforms. See [build_ios.md](build_ios.md) for detailed instructions.

### Quick Start
```bash
# Install Kivy and iOS tools
pip install kivy kivymd kivy-ios

# Build iOS project
toolchain create SongEditor2 .
cd SongEditor2-ios
toolchain run python main.py
```

### Key Considerations
- **Performance:** iOS has stricter memory and performance constraints
- **Permissions:** Proper audio and file access permissions required
- **App Store:** Code signing and App Store Connect setup required

## Android Build

### Overview
Building for Android requires adapting the PySide6-based application for mobile platforms. See [build_android.md](build_android.md) for detailed instructions.

### Quick Start
```bash
# Install Kivy and Buildozer
pip install kivy kivymd buildozer

# Initialize and configure buildozer
buildozer init
# Edit buildozer.spec as needed

# Build Android APK
buildozer android debug
```

### Key Considerations
- **Permissions:** Android requires explicit permission requests
- **Performance:** Background processing and memory management critical
- **Play Store:** Google Play Console setup and app signing required

## Cross-Platform Development

### Shared Code Structure
```
song_editor/
├── core/           # Core functionality (shared across platforms)
├── processing/     # Audio processing (shared)
├── export/         # Export functionality (shared)
├── models/         # Data models (shared)
├── services/       # External services (shared)
└── ui/            # Platform-specific UI
    ├── desktop/   # PySide6 UI (macOS/Windows)
    ├── mobile/    # Kivy UI (iOS/Android)
    └── web/       # Web UI (optional)
```

### Platform Abstraction
```python
# platform_utils.py
import platform
import sys

def get_platform():
    """Get current platform information"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor()
    }

def is_mobile():
    """Check if running on mobile platform"""
    return platform.system() in ['iOS', 'Android']

def is_desktop():
    """Check if running on desktop platform"""
    return platform.system() in ['Darwin', 'Windows', 'Linux']
```

## Testing

### Desktop Testing
```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run GUI tests
python -m pytest tests/gui/
```

### Mobile Testing
```bash
# iOS Simulator
xcrun simctl boot "iPhone 14"
toolchain run python main.py

# Android Emulator
emulator -avd Pixel_4_API_30
buildozer android debug deploy run
```

### Performance Testing
```bash
# Memory usage
python -m memory_profiler song_editor/app.py

# CPU profiling
python -m cProfile -o profile.stats song_editor/app.py
```

## Deployment

### Desktop Deployment

#### macOS
- **App Store:** Requires Apple Developer account and App Store Connect setup
- **Direct Distribution:** DMG files can be distributed directly
- **Homebrew:** Can be packaged as a Homebrew formula

#### Windows
- **Microsoft Store:** Requires Microsoft Developer account
- **Direct Distribution:** Installer files (.exe) can be distributed directly
- **Chocolatey:** Can be packaged as a Chocolatey package

### Mobile Deployment

#### iOS
- **App Store:** Primary distribution method
- **TestFlight:** Beta testing
- **Enterprise:** Internal distribution

#### Android
- **Google Play Store:** Primary distribution method
- **Internal Testing:** Google Play Console internal testing
- **APK Distribution:** Direct APK distribution

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Clean build artifacts
rm -rf build/ dist/ __pycache__/

# Reinstall dependencies
pip uninstall -r requirements.txt
pip install -r requirements.txt

# Check Python version
python --version
```

#### Runtime Errors
```bash
# Check dependencies
pip list

# Verify imports
python -c "import song_editor; print('Import successful')"

# Debug mode
python -v song_editor/app.py
```

#### Platform-Specific Issues

**macOS:**
- Gatekeeper blocking: `xattr -cr "Song Editor 2.app"`
- Code signing issues: Check certificates in Keychain Access

**Windows:**
- Missing DLLs: Install Visual C++ redistributables
- Antivirus blocking: Add to exclusion list

**iOS:**
- Provisioning profile issues: Check Apple Developer account
- Code signing: Verify certificates and provisioning profiles

**Android:**
- Build tool version conflicts: Update Android SDK
- Permission issues: Check AndroidManifest.xml

### Debug Tools

#### Desktop
- **macOS:** Console.app, Instruments
- **Windows:** Event Viewer, Process Monitor
- **Linux:** strace, gdb

#### Mobile
- **iOS:** Xcode Instruments, Console.app
- **Android:** Android Studio Profiler, Logcat

### Getting Help

1. **Check Issues:** Look for similar issues in the project repository
2. **Platform Forums:** Check platform-specific developer forums
3. **Documentation:** Review platform-specific documentation
4. **Community:** Ask in relevant developer communities

## Contributing

### Development Setup
```bash
# Fork and clone the repository
git clone <your-fork-url>
cd Song_Editor_2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Make changes and test
python song_editor/app.py
```

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Add tests for new functionality

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the project repository
- Check the documentation
- Review the troubleshooting section above
