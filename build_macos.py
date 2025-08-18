#!/usr/bin/env python3
"""
Build script for macOS Song Editor 2
Creates a standalone .app bundle using PyInstaller
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def install_dependencies():
    """Install required build dependencies"""
    print("Installing build dependencies...")
    
    # Install PyInstaller
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Install additional dependencies for audio processing
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller-hooks-contrib"])

def create_spec_file():
    """Create PyInstaller spec file for the application"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(os.path.dirname(os.path.abspath(SPECPATH)))
sys.path.insert(0, str(project_root))

block_cipher = None

# Collect all necessary data files
datas = [
    ('requirements.txt', '.'),
]

# Collect hidden imports
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'numpy',
    'scipy',
    'soundfile',
    'sounddevice',
    'faster_whisper',
    'librosa',
    'mido',
    'python_rtmidi',
    'praat_parselmouth',
    'requests',
    'aiohttp',
    'matplotlib',
    'torch',
    'demucs',
    'ctranslate2',
    'numba',
    'llvmlite',
    'tenacity',
    'yaml',
    'song_editor',
    'song_editor.core',
    'song_editor.export',
    'song_editor.models',
    'song_editor.processing',
    'song_editor.services',
    'song_editor.ui',
]

# Exclude unnecessary modules to reduce bundle size
excludes = [
    'tkinter',
    'test',
    'distutils',
    'setuptools',
    'pydoc',
    'doctest',
    'unittest',
    'email',
    'html',
    'http',
    'urllib',
    'xml',
    'pdb',
    'pydoc_data',
    'multiprocessing.pool',
    'multiprocessing.managers',
    'multiprocessing.synchronize',
    'multiprocessing.heap',
    'multiprocessing.popen_fork',
    'multiprocessing.popen_forkserver',
    'multiprocessing.popen_spawn_posix',
    'multiprocessing.popen_spawn_win32',
    'multiprocessing.sharedctypes',
    'multiprocessing.spawn',
    'multiprocessing.util',
]

a = Analysis(
    ['song_editor/app.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Song Editor 2',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Song Editor 2',
)

app = BUNDLE(
    coll,
    name='Song Editor 2.app',
    icon=None,  # Add icon path here if you have one
    bundle_identifier='com.songeditor.app',
    info_plist={
        'CFBundleName': 'Song Editor 2',
        'CFBundleDisplayName': 'Song Editor 2',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleIdentifier': 'com.songeditor.app',
        'CFBundleExecutable': 'Song Editor 2',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'LSMinimumSystemVersion': '10.14.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'NSMicrophoneUsageDescription': 'This app needs microphone access for audio recording and transcription.',
        'NSCameraUsageDescription': 'This app may need camera access for video processing.',
    },
)
'''
    
    with open('Song_Editor_2.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: Song_Editor_2.spec")

def build_app():
    """Build the macOS application bundle"""
    print("Building macOS application bundle...")
    
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Run PyInstaller
    run_command([sys.executable, '-m', 'PyInstaller', 'Song_Editor_2.spec', '--clean'])
    
    print("Build completed successfully!")
    print("Application bundle created at: dist/Song Editor 2.app")

def create_dmg():
    """Create a DMG installer (optional)"""
    print("Creating DMG installer...")
    
    # Check if create-dmg is available
    result = subprocess.run(['which', 'create-dmg'], capture_output=True, text=True)
    if result.returncode != 0:
        print("create-dmg not found. Installing...")
        try:
            run_command(['brew', 'install', 'create-dmg'])
        except:
            print("Failed to install create-dmg. Skipping DMG creation.")
            print("You can install it manually with: brew install create-dmg")
            return
    
    # Create DMG
    dmg_name = "Song_Editor_2_v2.0.0_macOS.dmg"
    try:
        run_command([
            'create-dmg',
            '--volname', 'Song Editor 2',
            '--window-pos', '200', '120',
            '--window-size', '600', '400',
            '--icon-size', '100',
            '--icon', 'Song Editor 2.app', '175', '120',
            '--hide-extension', 'Song Editor 2.app',
            '--app-drop-link', '425', '120',
            dmg_name,
            'dist/'
        ])
        print(f"DMG created: {dmg_name}")
    except Exception as e:
        print(f"Failed to create DMG: {e}")
        print("DMG creation skipped. Application bundle is still available.")

def main():
    """Main build process"""
    print("=== Song Editor 2 macOS Build Process ===")
    
    # Check if we're on macOS
    if sys.platform != 'darwin':
        print("Error: This build script is for macOS only")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Create spec file
    create_spec_file()
    
    # Build the app
    build_app()
    
    # Create DMG (optional)
    create_dmg_option = input("Create DMG installer? (y/n): ").lower().strip()
    if create_dmg_option == 'y':
        create_dmg()
    
    print("=== Build process completed! ===")
    print("Your application is ready at: dist/Song Editor 2.app")

if __name__ == "__main__":
    main()
