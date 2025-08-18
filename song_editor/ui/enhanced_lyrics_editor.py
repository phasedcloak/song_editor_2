import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QPushButton, QScrollArea, QFrame, QSplitter, QCheckBox,
    QToolTip, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QPalette,
    QTextDocument, QTextBlockFormat, QTextBlock
)

import cmudict
import pronouncing

from ..models.lyrics import WordRow


@dataclass
class RhymeInfo:
    """Information about rhyming words"""
    word: str
    pronunciation: List[str]
    rhyme_type: str  # 'perfect', 'near', 'none'
    rhyme_group: str  # Group identifier for same color


class SyllableCounter:
    """Professional syllable counting using cmudict"""
    
    def __init__(self):
        self.cmu = cmudict.dict()
        self.cache = {}
    
    def count_syllables(self, word: str) -> int:
        """Count syllables in a word using cmudict"""
        if word in self.cache:
            return self.cache[word]
        
        # Clean the word
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        
        if clean_word in self.cmu:
            # Get the first pronunciation
            pronunciation = self.cmu[clean_word][0]
            # Count syllables (each vowel sound is a syllable)
            syllable_count = len([p for p in pronunciation if p[-1].isdigit()])
            self.cache[word] = syllable_count
            return syllable_count
        else:
            # Fallback: estimate syllables by counting vowel groups
            vowel_groups = len(re.findall(r'[aeiouy]+', clean_word))
            self.cache[word] = max(1, vowel_groups)
            return max(1, vowel_groups)


class RhymeAnalyzer:
    """Analyze rhyming patterns using pronouncing library"""
    
    def __init__(self):
        self.cache = {}
    
    def get_pronunciation(self, word: str) -> List[str]:
        """Get pronunciation for a word"""
        if word in self.cache:
            return self.cache[word]
        
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        pronunciation = pronouncing.phones_for_word(clean_word)
        
        if pronunciation:
            self.cache[word] = pronunciation[0]
            return pronunciation[0]
        else:
            # Fallback: return empty pronunciation
            self.cache[word] = ""
            return ""
    
    def are_perfect_rhymes(self, word1: str, word2: str) -> bool:
        """Check if two words are perfect rhymes"""
        if word1 == word2:
            return False
        
        pron1 = self.get_pronunciation(word1)
        pron2 = self.get_pronunciation(word2)
        
        if not pron1 or not pron2:
            return False
        
        return pronouncing.rhyme(pron1, pron2)
    
    def are_near_rhymes(self, word1: str, word2: str) -> bool:
        """Check if two words are near rhymes (assonance)"""
        if word1 == word2:
            return False
        
        pron1 = self.get_pronunciation(word1)
        pron2 = self.get_pronunciation(word2)
        
        if not pron1 or not pron2:
            return False
        
        # Check for assonance (same vowel sounds)
        vowels1 = pronouncing.stresses(pron1)
        vowels2 = pronouncing.stresses(pron2)
        
        return vowels1 == vowels2 and len(vowels1) > 0
    
    def find_rhymes(self, target_word: str, word_list: List[str]) -> Dict[str, List[str]]:
        """Find perfect and near rhymes for a target word"""
        perfect_rhymes = []
        near_rhymes = []
        
        for word in word_list:
            if word.lower() == target_word.lower():
                continue
            
            if self.are_perfect_rhymes(target_word, word):
                perfect_rhymes.append(word)
            elif self.are_near_rhymes(target_word, word):
                near_rhymes.append(word)
        
        return {
            'perfect': perfect_rhymes,
            'near': near_rhymes
        }


class AudioPlaybackThread(QThread):
    """Thread for playing audio segments"""
    
    playback_finished = Signal()
    
    def __init__(self, audio_path: str, start_time: float, duration: float):
        super().__init__()
        self.audio_path = audio_path
        self.start_time = start_time
        self.duration = duration
        self.player = None
    
    def run(self):
        """Play audio segment"""
        try:
            from ..core.audio_player import AudioPlayer
            self.player = AudioPlayer()
            self.player.load_audio(self.audio_path)
            self.player.play_segment(self.start_time, self.duration)
            
            # Wait for playback to finish
            import time
            time.sleep(self.duration)
            
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            if self.player:
                self.player.stop()
            self.playback_finished.emit()
    
    def stop_playback(self):
        """Stop playback"""
        if self.player:
            self.player.stop()
        self.playback_finished.emit()


class SyllablePanel(QWidget):
    """Left panel showing syllable counts for each line"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.syllable_counter = SyllableCounter()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel("Syllables")
        header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                padding: 5px;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        layout.addWidget(header)
        
        # Scroll area for syllable counts
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setMaximumWidth(100)
        
        # Container for syllable labels
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(2)
        self.container_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        
        # Set fixed width
        self.setMaximumWidth(120)
        self.setMinimumWidth(80)
    
    def update_syllable_counts(self, lyrics_text: str):
        """Update syllable counts for the lyrics"""
        # Clear existing labels
        for i in reversed(range(self.container_layout.count())):
            child = self.container_layout.itemAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        if not lyrics_text.strip():
            return
        
        lines = lyrics_text.split('\n')
        
        for line in lines:
            if not line.strip():
                # Empty line
                label = QLabel("")
                label.setMinimumHeight(20)
                self.container_layout.addWidget(label)
                continue
            
            # Count syllables in this line
            words = re.findall(r'\b\w+\b', line.lower())
            total_syllables = sum(self.syllable_counter.count_syllables(word) for word in words)
            
            # Create label
            label = QLabel(f"{total_syllables}")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #e8f4f8;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 3px;
                    font-weight: bold;
                    color: #333;
                }
            """)
            label.setMinimumHeight(20)
            self.container_layout.addWidget(label)
        
        # Add stretch at the end
        self.container_layout.addStretch()


class RhymePanel(QWidget):
    """Right panel showing rhyming suggestions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rhyme_analyzer = RhymeAnalyzer()
        self.current_word = ""
        self.all_words = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel("Rhymes")
        header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                padding: 5px;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        layout.addWidget(header)
        
        # Current word display
        self.current_word_label = QLabel("Select a word")
        self.current_word_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }
        """)
        self.current_word_label.setWordWrap(True)
        layout.addWidget(self.current_word_label)
        
        # Perfect rhymes section
        perfect_header = QLabel("Perfect Rhymes:")
        perfect_header.setStyleSheet("font-weight: bold; color: #28a745;")
        layout.addWidget(perfect_header)
        
        self.perfect_rhymes_text = QTextEdit()
        self.perfect_rhymes_text.setMaximumHeight(100)
        self.perfect_rhymes_text.setReadOnly(True)
        self.perfect_rhymes_text.setStyleSheet("""
            QTextEdit {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.perfect_rhymes_text)
        
        # Near rhymes section
        near_header = QLabel("Near Rhymes:")
        near_header.setStyleSheet("font-weight: bold; color: #ffc107;")
        layout.addWidget(near_header)
        
        self.near_rhymes_text = QTextEdit()
        self.near_rhymes_text.setMaximumHeight(100)
        self.near_rhymes_text.setReadOnly(True)
        self.near_rhymes_text.setStyleSheet("""
            QTextEdit {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.near_rhymes_text)
        
        # Set fixed width
        self.setMaximumWidth(200)
        self.setMinimumWidth(150)
    
    def update_rhymes(self, target_word: str, all_words: List[str]):
        """Update rhyming suggestions for the target word"""
        self.current_word = target_word
        self.all_words = all_words
        
        if not target_word:
            self.current_word_label.setText("Select a word")
            self.perfect_rhymes_text.clear()
            self.near_rhymes_text.clear()
            return
        
        self.current_word_label.setText(f"Word: {target_word}")
        
        # Find rhymes
        rhymes = self.rhyme_analyzer.find_rhymes(target_word, all_words)
        
        # Display perfect rhymes
        perfect_rhymes = rhymes['perfect']
        if perfect_rhymes:
            self.perfect_rhymes_text.setPlainText(', '.join(perfect_rhymes))
        else:
            self.perfect_rhymes_text.setPlainText("None found")
        
        # Display near rhymes
        near_rhymes = rhymes['near']
        if near_rhymes:
            self.near_rhymes_text.setPlainText(', '.join(near_rhymes))
        else:
            self.near_rhymes_text.setPlainText("None found")


class EnhancedLyricsEditor(QWidget):
    """Enhanced lyrics editor with multi-line support, syllable counting, and rhyming"""
    
    lyrics_changed = Signal(str)
    play_audio_requested = Signal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_path = None
        self.lyrics_data = []
        self.rhyme_analyzer = RhymeAnalyzer()
        self.syllable_counter = SyllableCounter()
        self.playback_thread = None
        self.color_mode = "confidence"  # "confidence" or "rhyme"
        self.rhyme_groups = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create splitter for three panels
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Syllable counts
        self.syllable_panel = SyllablePanel()
        self.splitter.addWidget(self.syllable_panel)
        
        # Center panel: Main lyrics editor
        self.lyrics_panel = self.create_lyrics_panel()
        self.splitter.addWidget(self.lyrics_panel)
        
        # Right panel: Rhyming suggestions
        self.rhyme_panel = RhymePanel()
        self.splitter.addWidget(self.rhyme_panel)
        
        # Set splitter proportions
        self.splitter.setSizes([100, 400, 200])
        
        layout.addWidget(self.splitter)
    
    def create_lyrics_panel(self):
        """Create the main lyrics editing panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Color mode toggle
        self.color_mode_checkbox = QCheckBox("Color by Rhymes")
        self.color_mode_checkbox.toggled.connect(self.on_color_mode_changed)
        controls_layout.addWidget(self.color_mode_checkbox)
        
        # Play button
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.play_current_selection)
        controls_layout.addWidget(self.play_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Main text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter lyrics here...")
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.text_edit.mouseDoubleClickEvent = self.on_double_click
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Arial', sans-serif;
                font-size: 14px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        layout.addWidget(self.text_edit)
        
        return panel
    
    def set_audio_path(self, audio_path: str):
        """Set the audio file path for playback"""
        self.audio_path = audio_path
    
    def set_lyrics_data(self, lyrics_data: List[WordRow]):
        """Set lyrics data and update display"""
        self.lyrics_data = lyrics_data
        
        # Convert to text format
        text_lines = []
        current_line = []
        
        for word in lyrics_data:
            # Add chord if available
            word_text = word.text
            if word.chord:
                word_text += f"[{word.chord}]"
            
            current_line.append(word_text)
            
            # Check if this word ends with punctuation that suggests end of line
            if word.text.endswith(('.', '!', '?', ':', ';')):
                text_lines.append(' '.join(current_line))
                current_line = []
        
        # Add any remaining words
        if current_line:
            text_lines.append(' '.join(current_line))
        
        # Set text in editor
        self.text_edit.setPlainText('\n'.join(text_lines))
        
        # Update syllable counts
        self.update_syllable_counts()
        
        # Analyze rhymes for coloring
        self.analyze_rhymes()
    
    def on_text_changed(self):
        """Handle text changes"""
        text = self.text_edit.toPlainText()
        self.lyrics_changed.emit(text)
        
        # Update syllable counts
        self.update_syllable_counts()
        
        # Re-analyze rhymes
        self.analyze_rhymes()
        
        # Apply coloring
        self.apply_coloring()
    
    def update_syllable_counts(self):
        """Update syllable counts in the left panel"""
        text = self.text_edit.toPlainText()
        self.syllable_panel.update_syllable_counts(text)
    
    def analyze_rhymes(self):
        """Analyze rhyming patterns in the text"""
        text = self.text_edit.toPlainText()
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Group words by rhyme patterns
        self.rhyme_groups = {}
        group_id = 0
        
        for i, word1 in enumerate(words):
            if word1 in self.rhyme_groups:
                continue
            
            # Find all words that rhyme with this word
            rhyming_words = []
            for j, word2 in enumerate(words):
                if i != j and self.rhyme_analyzer.are_perfect_rhymes(word1, word2):
                    rhyming_words.append(word2)
            
            if rhyming_words:
                # Create a rhyme group
                group_id += 1
                group_name = f"group_{group_id}"
                self.rhyme_groups[word1] = group_name
                for word in rhyming_words:
                    self.rhyme_groups[word] = group_name
    
    def apply_coloring(self):
        """Apply color coding based on current mode"""
        if self.color_mode == "confidence":
            self.apply_confidence_coloring()
        else:
            self.apply_rhyme_coloring()
    
    def apply_confidence_coloring(self):
        """Apply confidence-based color coding"""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        for word_data in self.lyrics_data:
            # Calculate color based on confidence
            confidence = word_data.confidence
            red = int(255 * (1.0 - confidence))
            green = int(255 * confidence)
            color = QColor(red, green, 0)
            
            # Create format
            format = QTextCharFormat()
            format.setForeground(color)
            
            # Find and format the word
            word_text = word_data.text
            if word_data.chord:
                word_text += f"[{word_data.chord}]"
            
            # Search for the word and apply formatting
            search_cursor = self.text_edit.document().find(word_text, cursor)
            if not search_cursor.isNull():
                search_cursor.mergeCharFormat(format)
    
    def apply_rhyme_coloring(self):
        """Apply rhyme-based color coding"""
        # Define colors for rhyme groups
        colors = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green
            QColor(0, 0, 255),    # Blue
            QColor(255, 165, 0),  # Orange
            QColor(128, 0, 128),  # Purple
            QColor(255, 192, 203), # Pink
            QColor(0, 255, 255),  # Cyan
            QColor(255, 255, 0),  # Yellow
        ]
        
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        # Group words by their rhyme group
        group_words = {}
        for word, group in self.rhyme_groups.items():
            if group not in group_words:
                group_words[group] = []
            group_words[group].append(word)
        
        # Apply colors to each group
        for i, (group_name, words) in enumerate(group_words.items()):
            if i >= len(colors):
                break
            
            color = colors[i]
            format = QTextCharFormat()
            format.setForeground(color)
            format.setFontWeight(QFont.Bold)
            
            # Apply formatting to all words in this group
            for word in words:
                search_cursor = self.text_edit.document().find(word, cursor)
                if not search_cursor.isNull():
                    search_cursor.mergeCharFormat(format)
    
    def on_color_mode_changed(self, checked: bool):
        """Handle color mode toggle"""
        self.color_mode = "rhyme" if checked else "confidence"
        self.apply_coloring()
    
    def on_double_click(self, event):
        """Handle double-click to play audio"""
        cursor = self.text_edit.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        
        # Find the word in lyrics data and play audio
        for word_data in self.lyrics_data:
            if word_data.text.lower() == word.lower():
                start_time = word_data.start
                end_time = word_data.end
                duration = end_time - start_time
                self.play_audio_requested.emit(start_time, duration)
                break
        
        # Also update rhyme panel
        self.update_rhyme_panel(word)
        
        # Call parent's double-click handler
        super().mouseDoubleClickEvent(event)
    
    def update_rhyme_panel(self, word: str):
        """Update the rhyme panel with suggestions for the selected word"""
        text = self.text_edit.toPlainText()
        all_words = re.findall(r'\b\w+\b', text.lower())
        self.rhyme_panel.update_rhymes(word, all_words)
    
    def play_current_selection(self):
        """Play audio for the currently selected text"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            # Find the corresponding audio segment
            for word_data in self.lyrics_data:
                if word_data.text in selected_text:
                    start_time = word_data.start
                    end_time = word_data.end
                    duration = end_time - start_time
                    self.play_audio_requested.emit(start_time, duration)
                    break
    
    def get_lyrics_text(self) -> str:
        """Get the current lyrics text"""
        return self.text_edit.toPlainText()
    
    def set_font(self, font: QFont):
        """Set font for the text editor"""
        self.text_edit.setFont(font)
