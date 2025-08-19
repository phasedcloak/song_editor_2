#!/usr/bin/env python3
"""
Simple test script for the Enhanced Lyrics Editor (without triggering text changes)
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QFont

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from song_editor.ui.enhanced_lyrics_editor import EnhancedLyricsEditor
from song_editor.models.lyrics import WordRow


def create_test_data():
    """Create test lyrics data"""
    test_words = [
        WordRow("Hello", 0.0, 0.5, 0.95, "C"),
        WordRow("world", 0.5, 1.0, 0.92, "Am"),
        WordRow("how", 1.0, 1.5, 0.89, "F"),
        WordRow("are", 1.5, 2.0, 0.91, "G"),
        WordRow("you", 2.0, 2.5, 0.94, "C"),
        WordRow("today", 2.5, 3.0, 0.88, "Am"),
        WordRow("I", 3.0, 3.3, 0.96, "F"),
        WordRow("hope", 3.3, 3.8, 0.93, "G"),
        WordRow("you", 3.8, 4.1, 0.90, "C"),
        WordRow("are", 4.1, 4.4, 0.87, "Am"),
        WordRow("well", 4.4, 4.9, 0.89, "F"),
    ]
    return test_words


def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Enhanced Lyrics Editor Simple Test")
    window.resize(1000, 600)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # Create layout
    layout = QVBoxLayout(central_widget)
    
    # Create enhanced lyrics editor
    editor = EnhancedLyricsEditor()
    layout.addWidget(editor)
    
    # Set test data (this will trigger the initial setup)
    test_data = create_test_data()
    
    # Disconnect text change signal temporarily to avoid recursion
    editor.text_edit.textChanged.disconnect()
    
    # Set the data
    editor.set_lyrics_data(test_data)
    
    # Reconnect the signal
    editor.text_edit.textChanged.connect(editor.on_text_changed)
    
    # Set font
    font = QFont("Arial", 14)
    editor.set_font(font)
    
    # Show window
    window.show()
    
    print("Enhanced Lyrics Editor Simple Test")
    print("Features to test:")
    print("1. Multi-line lyrics display")
    print("2. Left panel: Syllable counts for each line")
    print("3. Right panel: Double-click a word to see rhyming suggestions")
    print("4. Toggle 'Color by Rhymes' checkbox to switch between confidence and rhyme coloring")
    print("5. Double-click words to play audio (if audio file is set)")
    print("\nNote: This version avoids the recursion issue by temporarily disconnecting text change signals.")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
