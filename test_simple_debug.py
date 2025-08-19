#!/usr/bin/env python3

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
    ]
    return test_words


def main():
    """Main test function"""
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Simple Debug Test")
    window.resize(800, 400)
    
    # Create central widget
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    # Create layout
    layout = QVBoxLayout(central_widget)
    
    # Create enhanced lyrics editor
    editor = EnhancedLyricsEditor()
    layout.addWidget(editor)
    
    # Set test data
    test_data = create_test_data()
    print(f"Test data: {len(test_data)} words")
    for word in test_data:
        print(f"  {word.text} [{word.chord}]")
    
    # Set the data
    editor.set_lyrics_data(test_data)
    
    # Check what text was set
    current_text = editor.text_edit.toPlainText()
    print(f"Current text in editor: '{current_text}'")
    
    # Show window
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
