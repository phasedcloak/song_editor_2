#!/usr/bin/env python3
"""
Test script for Song Data Import/Export functionality
"""

import json
import os
from pathlib import Path
from song_editor.models.song_data_importer import SongDataImporter, SongData, ChordData, NoteData, SegmentData
from song_editor.models.lyrics import WordRow

def test_song_data_import():
    """Test the song data import functionality"""
    
    # Create a test song data file
    test_data = {
        "metadata": {
            "version": "2.0.0",
            "created_at": "2024-08-15T14:30:00Z",
            "source_audio": "/path/to/test_song.wav",
            "processing_tool": "Test Tool",
            "confidence_threshold": 0.7
        },
        "words": [
            {
                "text": "Hello",
                "start": 0.5,
                "end": 0.8,
                "confidence": 0.95,
                "chord": {
                    "symbol": "C",
                    "root": "C",
                    "quality": "maj",
                    "bass": None,
                    "confidence": 0.88
                }
            },
            {
                "text": "world",
                "start": 0.8,
                "end": 1.2,
                "confidence": 0.92,
                "chord": {
                    "symbol": "Am",
                    "root": "A",
                    "quality": "min",
                    "bass": None,
                    "confidence": 0.85
                }
            }
        ],
        "chords": [
            {
                "symbol": "C",
                "root": "C",
                "quality": "maj",
                "bass": None,
                "start": 0.0,
                "end": 0.8,
                "confidence": 0.88
            },
            {
                "symbol": "Am",
                "root": "A",
                "quality": "min",
                "bass": None,
                "start": 0.8,
                "end": 1.2,
                "confidence": 0.85
            }
        ],
        "notes": [
            {
                "pitch_midi": 60,
                "pitch_name": "C4",
                "start": 0.5,
                "end": 0.8,
                "velocity": 80,
                "confidence": 0.85
            }
        ],
        "segments": [
            {
                "type": "verse",
                "label": "Verse 1",
                "start": 0.5,
                "end": 1.2,
                "confidence": 0.92
            }
        ]
    }
    
    # Write test data to file
    test_file = "test_song_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Created test file: {test_file}")
    
    # Test import
    importer = SongDataImporter()
    song_data = importer.import_song_data(test_file)
    
    if song_data:
        print("✅ Import successful!")
        print(f"  - Words: {len(song_data.words)}")
        print(f"  - Chords: {len(song_data.chords)}")
        print(f"  - Notes: {len(song_data.notes)}")
        print(f"  - Segments: {len(song_data.segments)}")
        
        # Test export
        export_file = "test_export_song_data.json"
        if importer.export_song_data(song_data, export_file):
            print(f"✅ Export successful: {export_file}")
        else:
            print("❌ Export failed")
    else:
        print("❌ Import failed")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
    if os.path.exists(export_file):
        os.remove(export_file)

def test_file_discovery():
    """Test the file discovery functionality"""
    
    # Create test files
    test_files = [
        "song.wav",
        "song.song_data",
        "song.song_data.json",
        "song.json"
    ]
    
    for file in test_files:
        with open(file, 'w') as f:
            f.write("test")
    
    importer = SongDataImporter()
    
    # Test finding song data file
    found_file = importer.find_song_data_file("song.wav")
    if found_file:
        print(f"✅ Found song data file: {found_file}")
    else:
        print("❌ No song data file found")
    
    # Clean up
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)

if __name__ == "__main__":
    print("Testing Song Data Import/Export functionality...")
    print("=" * 50)
    
    test_song_data_import()
    print()
    test_file_discovery()
    
    print("\n✅ All tests completed!")
