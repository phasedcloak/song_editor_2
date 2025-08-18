#!/usr/bin/env python3
"""
Test script for Block View functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from song_editor.models.lyrics import WordRow
from song_editor.ui.block_view import BlockView, BlockData
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

def create_test_data():
    """Create test song data"""
    words = []
    chords = []
    
    # Create test words with timing
    test_lyrics = [
        ("Hello", 0.5, 1.0),
        ("world", 1.0, 1.5),
        ("how", 1.5, 2.0),
        ("are", 2.0, 2.5),
        ("you", 2.5, 3.0),
        ("today", 3.0, 3.5),
        ("I", 3.5, 4.0),
        ("hope", 4.0, 4.5),
        ("you", 4.5, 5.0),
        ("are", 5.0, 5.5),
        ("doing", 5.5, 6.0),
        ("well", 6.0, 6.5),
        ("and", 6.5, 7.0),
        ("feeling", 7.0, 7.5),
        ("great", 7.5, 8.0),
        ("about", 8.0, 8.5),
        ("this", 8.5, 9.0),
        ("new", 9.0, 9.5),
        ("feature", 9.5, 10.0),
        ("that", 10.0, 10.5),
        ("we", 10.5, 11.0),
        ("just", 11.0, 11.5),
        ("created", 11.5, 12.0),
        ("for", 12.0, 12.5),
        ("you", 12.5, 13.0),
        ("to", 13.0, 13.5),
        ("test", 13.5, 14.0),
        ("and", 14.0, 14.5),
        ("enjoy", 14.5, 15.0),
    ]
    
    for text, start, end in test_lyrics:
        word = WordRow(text, start, end, 0.9)
        words.append(word)
    
    # Create test chords
    from song_editor.processing.chords import DetectedChord
    test_chords = [
        ("C", 0.0, 2.0),
        ("Am", 2.0, 4.0),
        ("F", 4.0, 6.0),
        ("G", 6.0, 8.0),
        ("C", 8.0, 10.0),
        ("Am", 10.0, 12.0),
        ("F", 12.0, 14.0),
        ("G", 14.0, 16.0),
    ]
    
    for chord_name, start, end in test_chords:
        chord = DetectedChord(name=chord_name, start=start, end=end, confidence=0.8)
        chords.append(chord)
    
    # Create Gemini alternatives
    gemini_words = []
    for i, (text, start, end) in enumerate(test_lyrics):
        word = WordRow(f"Gemini_{text}", start, end, 0.9)
        gemini_words.append(word)
    
    gemini_chords = []
    for chord_name, start, end in test_chords:
        chord = DetectedChord(name=f"Gemini_{chord_name}", start=start, end=end, confidence=0.8)
        gemini_chords.append(chord)
    
    return words, chords, gemini_words, gemini_chords

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Block View Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create block view
        self.block_view = BlockView()
        self.block_view.data_updated.connect(self.on_data_updated)
        
        # Add test button
        test_btn = QPushButton("Load Test Data")
        test_btn.clicked.connect(self.load_test_data)
        layout.addWidget(test_btn)
        
        # Add block view
        layout.addWidget(self.block_view)
        
        # Load test data
        self.load_test_data()
    
    def load_test_data(self):
        """Load test data into block view"""
        words, chords, gemini_words, gemini_chords = create_test_data()
        
        # Set a dummy audio path
        self.block_view.set_audio_path("/path/to/test/audio.wav")
        
        # Create blocks from data
        self.block_view.create_blocks_from_data(words, chords, gemini_words, gemini_chords)
        
        print("Test data loaded into block view")
    
    def on_data_updated(self, updated_blocks):
        """Handle data updates"""
        print(f"Data updated: {len(updated_blocks)} blocks")
        for i, block in enumerate(updated_blocks):
            print(f"Block {i}: {block.local_chord} - {block.local_chord_edit.text()}")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    window = TestWindow()
    window.show()
    
    print("Block View Test Window opened")
    print("Features to test:")
    print("1. View 20-second blocks of song data")
    print("2. Edit chords and lyrics")
    print("3. Compare local vs Gemini data")
    print("4. Audio playback (if audio file is available)")
    print("5. Save changes")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
