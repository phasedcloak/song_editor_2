# Installation Guide for New Features

## Overview

This guide covers the installation of additional libraries needed for the new Song Data Import/Export and Block View features in Song Editor 2.

## Required Libraries

### Core Dependencies (Already in requirements.txt)
Most of the required libraries are already included in your existing `requirements.txt`. The new features primarily use:
- `PySide6` (already installed)
- `json` (built-in)
- `pathlib` (built-in)
- `dataclasses` (built-in)

### Optional Enhancements

#### 1. JSON Schema Validation
```bash
pip install jsonschema>=4.17.3
```
**Purpose**: Validate song data files against the schema
**Benefit**: Catch data format errors early

#### 2. Better Data Validation
```bash
pip install pydantic>=2.0.0
```
**Purpose**: Enhanced data validation and serialization
**Benefit**: More robust data handling

#### 3. UI Styling (Optional)
```bash
pip install qt-material>=2.14
```
**Purpose**: Modern Material Design theme for Qt
**Benefit**: Better visual appearance

#### 4. Testing Framework
```bash
pip install pytest>=7.0.0 pytest-qt>=4.2.0
```
**Purpose**: Test the new features
**Benefit**: Ensure functionality works correctly

## Installation Commands

### Quick Install (All Optional Features)
```bash
# Install all optional enhancements
pip install jsonschema>=4.17.3 pydantic>=2.0.0 qt-material>=2.14 pytest>=7.0.0 pytest-qt>=4.2.0
```

### Minimal Install (Core Features Only)
```bash
# The new features work with existing libraries
# No additional installation required for basic functionality
```

### Development Install
```bash
# Install development tools
pip install ipython>=8.0.0 jupyter>=1.0.0 loguru>=0.7.0
```

## Platform-Specific Notes

### macOS
```bash
# If you encounter issues with PyAudio
brew install portaudio
pip install pyaudio
```

### Windows
```bash
# PyAudio might need Visual C++ build tools
# Consider using conda instead:
conda install pyaudio
```

### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

## Verification

### Test Song Data Import/Export
```bash
python test_song_data_import.py
```
Expected output:
```
Testing Song Data Import/Export functionality...
==================================================
Created test file: test_song_data.json
✅ Import successful!
  - Words: 2
  - Chords: 2
  - Notes: 1
  - Segments: 1
✅ Export successful: test_export_song_data.json
✅ Found song data file: song.song_data
✅ All tests completed!
```

### Test Block View (if PySide6 is available)
```bash
python test_block_view.py
```
Expected output:
```
Block View Test Window opened
Features to test:
1. View 20-second blocks of song data
2. Edit chords and lyrics
3. Compare local vs Gemini data
4. Audio playback (if audio file is available)
5. Save changes
```

## Troubleshooting

### Common Issues

#### 1. PySide6 Not Found
```bash
# Install PySide6 if not already installed
pip install PySide6>=6.7.0
```

#### 2. Audio Playback Issues
```bash
# Install audio dependencies
pip install pyaudio sounddevice
```

#### 3. JSON Schema Validation Errors
```bash
# Install jsonschema
pip install jsonschema>=4.17.3
```

#### 4. Import Errors
```bash
# Ensure you're in the correct directory
cd /path/to/Song_Editor_2
python -c "from song_editor.models.song_data_importer import SongDataImporter; print('✅ Import successful')"
```

### Environment Setup

#### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv song_editor_env

# Activate on macOS/Linux
source song_editor_env/bin/activate

# Activate on Windows
song_editor_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_new_features.txt
```

#### Conda Environment
```bash
# Create conda environment
conda create -n song_editor python=3.9
conda activate song_editor

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_new_features.txt
```

## Feature-Specific Requirements

### Song Data Import/Export
**Minimum Requirements**: None (uses built-in libraries)
**Recommended**: `jsonschema`, `pydantic`
**Optional**: `loguru` for better logging

### Block View
**Minimum Requirements**: `PySide6` (already installed)
**Recommended**: `qt-material` for better styling
**Optional**: `pytest-qt` for testing

### Audio Playback
**Minimum Requirements**: `sounddevice` (already in requirements.txt)
**Recommended**: `pyaudio` for better audio support
**Optional**: `librosa` for advanced audio processing

## Performance Considerations

### Lightweight Installation
If you want minimal dependencies:
```bash
# Only install what you need
pip install jsonschema  # For schema validation
```

### Full Feature Set
For all features and enhancements:
```bash
# Install everything
pip install -r requirements_new_features.txt
```

## Next Steps

After installation:

1. **Test the features**:
   ```bash
   python test_song_data_import.py
   ```

2. **Try the block view**:
   ```bash
   python test_block_view.py
   ```

3. **Run the main application**:
   ```bash
   python -m song_editor.app
   ```

4. **Create song data files** following the schema in `song_data_schema.json`

5. **Use the block view** for detailed editing and analysis

## Support

If you encounter issues:

1. Check that all dependencies are installed
2. Verify you're using the correct Python version (3.8+)
3. Ensure you're in the correct directory
4. Check the troubleshooting section above
5. Review the error messages for specific guidance
