#!/usr/bin/env python3
"""
Build script for Windows Song Editor 2
Creates a standalone executable using PyInstaller
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
    """Create PyInstaller spec file for Windows"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Song Editor 2',
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
    icon=None,  # Add icon path here if you have one
    version_file=None,  # Add version file path here if you have one
)
'''
    
    with open('Song_Editor_2_Windows.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file: Song_Editor_2_Windows.spec")

def build_exe():
    """Build the Windows executable"""
    print("Building Windows executable...")
    
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Run PyInstaller
    run_command([sys.executable, '-m', 'PyInstaller', 'Song_Editor_2_Windows.spec', '--clean'])
    
    print("Build completed successfully!")
    print("Executable created at: dist/Song Editor 2.exe")

def create_installer():
    """Create an NSIS installer (optional)"""
    print("Creating NSIS installer...")
    
    # Create NSIS script
    nsis_script = '''!include "MUI2.nsh"

Name "Song Editor 2"
OutFile "Song_Editor_2_v2.0.0_Windows.exe"
InstallDir "$PROGRAMFILES\\Song Editor 2"
InstallDirRegKey HKCU "Software\\Song Editor 2" ""

RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Song Editor 2" SecMain
    SetOutPath "$INSTDIR"
    File /r "dist\\Song Editor 2.exe"
    
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\\Song Editor 2"
    CreateShortCut "$SMPROGRAMS\\Song Editor 2\\Song Editor 2.lnk" "$INSTDIR\\Song Editor 2.exe"
    CreateShortCut "$SMPROGRAMS\\Song Editor 2\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    
    CreateShortCut "$DESKTOP\\Song Editor 2.lnk" "$INSTDIR\\Song Editor 2.exe"
    
    WriteRegStr HKCU "Software\\Song Editor 2" "" $INSTDIR
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2" "DisplayName" "Song Editor 2"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2" "DisplayIcon" "$INSTDIR\\Song Editor 2.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2" "Publisher" "Song Editor Team"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2" "DisplayVersion" "2.0.0"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\Song Editor 2.exe"
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\\Song Editor 2\\Song Editor 2.lnk"
    Delete "$SMPROGRAMS\\Song Editor 2\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\Song Editor 2"
    
    Delete "$DESKTOP\\Song Editor 2.lnk"
    
    DeleteRegKey HKCU "Software\\Song Editor 2"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Song Editor 2"
SectionEnd
'''
    
    with open('installer.nsi', 'w') as f:
        f.write(nsis_script)
    
    # Check if NSIS is installed
    try:
        run_command(['makensis', '--version'], check=False)
        run_command(['makensis', 'installer.nsi'])
        print("NSIS installer created: Song_Editor_2_v2.0.0_Windows.exe")
    except:
        print("NSIS not found. Please install NSIS to create an installer.")
        print("Download from: https://nsis.sourceforge.io/Download")

def main():
    """Main build process"""
    print("=== Song Editor 2 Windows Build Process ===")
    
    # Check if we're on Windows
    if sys.platform != 'win32':
        print("Error: This build script is for Windows only")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Create spec file
    create_spec_file()
    
    # Build the executable
    build_exe()
    
    # Create installer (optional)
    create_installer_option = input("Create NSIS installer? (y/n): ").lower().strip()
    if create_installer_option == 'y':
        create_installer()
    
    print("=== Build process completed! ===")
    print("Your executable is ready at: dist/Song Editor 2.exe")

if __name__ == "__main__":
    main()
