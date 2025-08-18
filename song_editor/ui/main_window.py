from __future__ import annotations

import os
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Slot, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QHBoxLayout,
	QFileDialog,
	QSplitter,
	QTableView,
	QToolBar,
	QStatusBar,
	QComboBox,
	QPushButton,
	QLabel,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QSlider,
)
from PySide6.QtCore import QDir

from ..core.audio_player import AudioPlayer
from ..processing.transcriber import Transcriber, Word
from ..processing.chords import ChordDetector, DetectedChord
from ..export.ccli import export_ccli
from ..export.midi_export import export_midi
from ..services.gemini_client import GeminiClient
from ..models.lyrics import WordRow
from ..models.song_data_importer import SongDataImporter, SongData
from ..processing.separate import separate_vocals_instrumental
from .block_view import BlockView
from .enhanced_lyrics_editor import EnhancedLyricsEditor


from PySide6.QtGui import QColor


class WordsTableModel(QAbstractTableModel):
	HEADERS = [
		"Word", "Start (s)", "End (s)", "Conf.", "Chord", "Alternatives"
	]
	
	# Gemini columns are hidden by default and shown only when Gemini processing is active
	GEMINI_HEADERS = [
		"Word", "Start (s)", "End (s)", "Conf.", "Chord", "Alternatives",
		"Gemini Word", "Gemini Chord"
	]

	def __init__(self, words: List[WordRow]):
		super().__init__()
		self._rows: List[WordRow] = words

	def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
		return len(self._rows)

	def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
		return len(self.HEADERS)

	def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
		if not index.isValid():
			return None
		row = self._rows[index.row()]
		col = index.column()
		if role == Qt.DisplayRole or role == Qt.EditRole:
			if col == 0:
				return row.text
			elif col == 1:
				return f"{row.start:.3f}"
			elif col == 2:
				return f"{row.end:.3f}"
			elif col == 3:
				return f"{row.confidence:.2f}"
			elif col == 4:
				return row.chord or ""
			elif col == 5:
				# Show alternatives in a compact format
				if row.alt_text:
					return f"<{row.alt_text}>"
				return ""
			elif col == 6 and hasattr(self, '_show_gemini_columns') and self._show_gemini_columns:
				# Gemini Word column
				return getattr(row, 'gemini_text', '') or ""
			elif col == 7 and hasattr(self, '_show_gemini_columns') and self._show_gemini_columns:
				# Gemini Chord column
				return getattr(row, 'gemini_chord', '') or ""
		elif role == Qt.ForegroundRole and col == 0:
			# color-coded confidence: 0.0 red -> 1.0 green
			c = max(0.0, min(1.0, row.confidence))
			red = int(255 * (1.0 - c))
			green = int(255 * c)
			return QColor(red, green, 0)
		return None

	def setData(self, index: QModelIndex, value, role: int = Qt.EditRole):  # type: ignore[override]
		if not index.isValid() or index.column() != 0 or role != Qt.EditRole:
			return False
		
		# Update the word text
		self._rows[index.row()].text = str(value)
		
		# Set confidence to 100% when user edits a word (indicating manual correction)
		self._rows[index.row()].confidence = 1.0
		
		# Emit data changed for both text and confidence columns
		self.dataChanged.emit(index, index, [Qt.DisplayRole])
		# Also emit for confidence column (column 3)
		confidence_index = self.index(index.row(), 3)
		self.dataChanged.emit(confidence_index, confidence_index, [Qt.DisplayRole])
		
		return True

	def flags(self, index: QModelIndex):  # type: ignore[override]
		fl = super().flags(index)
		if index.column() == 0:  # Only Word column is editable
			fl |= Qt.ItemIsEditable
		return fl

	def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[override]
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			# Use Gemini headers if Gemini processing is active
			if hasattr(self, '_show_gemini_columns') and self._show_gemini_columns:
				return self.GEMINI_HEADERS[section]
			else:
				return self.HEADERS[section]
		return super().headerData(section, orientation, role)
	
	def set_show_gemini_columns(self, show: bool) -> None:
		"""Show or hide Gemini columns"""
		self._show_gemini_columns = show
		# Emit layout changed to refresh the table
		self.layoutChanged.emit()
	
	def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
		# Return different column count based on whether Gemini columns are shown
		if hasattr(self, '_show_gemini_columns') and self._show_gemini_columns:
			return len(self.GEMINI_HEADERS)
		else:
			return len(self.HEADERS)

	def rows(self) -> List[WordRow]:
		return self._rows


class MainWindow(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("Song Editor 2")

		self.audio_path: Optional[str] = None
		self.player = AudioPlayer()
		self.transcriber = Transcriber()
		self.chord_detector = ChordDetector()
		self.gemini = GeminiClient()
		self.song_data_importer = SongDataImporter()
		self.detected_chords: list[DetectedChord] = []
		self.vocals_path: Optional[str] = None
		self.instrumental_path: Optional[str] = None
		self._gemini_thread: Optional[QThread] = None
		self.imported_song_data: Optional[SongData] = None

		self.words_model = WordsTableModel([])
		self.words_view = QTableView()
		self.words_view.setModel(self.words_model)
		# Hide confidence column toggle via context menu setting (start hidden) if desired
		self.words_view.setContextMenuPolicy(Qt.ActionsContextMenu)
		toggle_conf = QAction("Show/Hide Confidence", self)
		def _toggle_conf():
			cur = not self.words_view.isColumnHidden(3)
			self.words_view.setColumnHidden(3, cur)
		toggle_conf.triggered.connect(_toggle_conf)
		self.words_view.addAction(toggle_conf)
		# Start hidden per request
		self.words_view.setColumnHidden(3, True)
		self.words_view.doubleClicked.connect(self.on_row_double_clicked)
		self.words_view.setSelectionBehavior(QTableView.SelectRows)
		
		# Connect table view data changes to sync with block view
		self.words_model.dataChanged.connect(self.on_table_data_changed)

		# Block view for 20-second segments
		self.block_view = BlockView()
		self.block_view.data_updated.connect(self.on_block_data_updated)
		
		# Set audio path for block view if we already have one
		if hasattr(self, 'audio_path') and self.audio_path:
			self.block_view.set_audio_path(self.audio_path)
		
		# Enhanced lyrics editor
		self.enhanced_lyrics_editor = EnhancedLyricsEditor()
		self.enhanced_lyrics_editor.lyrics_changed.connect(self.on_enhanced_lyrics_changed)
		self.enhanced_lyrics_editor.play_audio_requested.connect(self.on_enhanced_play_audio_requested)
		
		# Set audio path for enhanced editor if we already have one
		if hasattr(self, 'audio_path') and self.audio_path:
			self.enhanced_lyrics_editor.set_audio_path(self.audio_path)

		self.status = QStatusBar()
		self.setStatusBar(self.status)

		# Top toolbar
		toolbar = QToolBar("Main")
		self.addToolBar(toolbar)
		open_act = QAction("Open Audio", self)
		open_act.triggered.connect(self.open_audio)
		toolbar.addAction(open_act)

		transcribe_act = QAction("Transcribe", self)
		transcribe_act.triggered.connect(self.run_transcription)
		toolbar.addAction(transcribe_act)

		chords_act = QAction("Detect Chords", self)
		chords_act.triggered.connect(self.run_chords)
		toolbar.addAction(chords_act)

		separate_act = QAction("Separate Stems", self)
		separate_act.triggered.connect(self.run_separation)
		toolbar.addAction(separate_act)

		gemini_act = QAction("Gemini Alt Lyrics", self)
		gemini_act.triggered.connect(self.generate_gemini_alt)
		toolbar.addAction(gemini_act)
		self.gemini_act = gemini_act

		gemini_audio_act = QAction("Gemini From Audio", self)
		gemini_audio_act.triggered.connect(self.generate_gemini_from_audio)
		toolbar.addAction(gemini_audio_act)
		self.gemini_audio_act = gemini_audio_act

		cloud_settings_act = QAction("Cloud Settings", self)
		cloud_settings_act.triggered.connect(self.open_cloud_settings)
		toolbar.addAction(cloud_settings_act)

		export_ccli_act = QAction("Export CCLI", self)
		export_ccli_act.triggered.connect(self.export_ccli_text)
		toolbar.addAction(export_ccli_act)

		export_midi_act = QAction("Export MIDI", self)
		export_midi_act.triggered.connect(self.export_midi)
		toolbar.addAction(export_midi_act)

		export_song_data_act = QAction("Export Song Data", self)
		export_song_data_act.triggered.connect(self.export_song_data)
		toolbar.addAction(export_song_data_act)
		
		# Add help menu
		help_menu = self.menuBar().addMenu("&Help")
		
		# Supported formats action
		formats_action = QAction("Supported Audio Formats", self)
		formats_action.triggered.connect(self.show_supported_formats)
		help_menu.addAction(formats_action)

		# Central layout
		container = QWidget()
		layout = QVBoxLayout(container)

		# Controls row
		controls = QHBoxLayout()
		self.model_combo = QComboBox()
		self.model_combo.addItems(["large-v2", "medium", "small", "base", "tiny"])
		controls.addWidget(QLabel("Model:"))
		controls.addWidget(self.model_combo)

		# View mode selector
		self.view_mode_combo = QComboBox()
		self.view_mode_combo.addItems(["Table View", "Block View", "Enhanced Lyrics Editor"])
		self.view_mode_combo.currentTextChanged.connect(self.on_view_mode_changed)
		controls.addWidget(QLabel("View:"))
		controls.addWidget(self.view_mode_combo)

		self.gemini_model_combo = QComboBox()
		self.gemini_model_combo.addItems([
			"gemini-2.5-flash",
			"gemini-1.5-flash",
			"gemini-1.5-pro",
			"gemini-1.5-pro-002",
			"gemini-2.0-flash-exp",
		])
		self.gemini_model_combo.setCurrentText("gemini-2.5-flash")
		controls.addWidget(QLabel("Gemini:"))
		controls.addWidget(self.gemini_model_combo)
		play_btn = QPushButton("Play/Pause")
		play_btn.clicked.connect(self.player.toggle_play_pause)
		controls.addWidget(play_btn)
		
		# Font controls
		controls.addWidget(QLabel("Font:"))
		self.font_combo = QComboBox()
		self.font_combo.addItems(["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana", "Georgia", "Palatino"])
		self.font_combo.setCurrentText("Arial")
		self.font_combo.currentTextChanged.connect(self.on_font_changed)
		controls.addWidget(self.font_combo)
		
		controls.addWidget(QLabel("Size:"))
		self.font_size_combo = QComboBox()
		self.font_size_combo.addItems(["10", "12", "14", "16", "18", "20", "24", "28", "32"])
		self.font_size_combo.setCurrentText("14")
		self.font_size_combo.currentTextChanged.connect(self.on_font_size_changed)
		controls.addWidget(self.font_size_combo)
		
		# Word playback duration control
		controls.addWidget(QLabel("Word Duration:"))
		self.word_duration_slider = QSlider(Qt.Horizontal)
		self.word_duration_slider.setMinimum(1)  # 1 second
		self.word_duration_slider.setMaximum(10)  # 10 seconds
		self.word_duration_slider.setValue(3)  # Default 3 seconds
		self.word_duration_slider.setMaximumWidth(100)
		self.word_duration_slider.valueChanged.connect(self.on_word_duration_changed)
		controls.addWidget(self.word_duration_slider)
		
		self.word_duration_label = QLabel("3.0s")
		controls.addWidget(self.word_duration_label)
		
		layout.addLayout(controls)

		# Create stacked widget for different views
		self.view_stack = QWidget()
		self.view_layout = QVBoxLayout(self.view_stack)
		
		# Add all views to the stack
		self.view_layout.addWidget(self.words_view)
		self.view_layout.addWidget(self.block_view)
		self.view_layout.addWidget(self.enhanced_lyrics_editor)
		
		# Start with table view visible
		self.block_view.hide()
		self.enhanced_lyrics_editor.hide()
		
		layout.addWidget(self.view_stack)

		self.setCentralWidget(container)

		# Default cloud chunking params
		self.gemini_chunk_seconds = 60
		self.gemini_sleep_between = 15

	def prepare_shutdown(self) -> None:
		# Called from app.aboutToQuit
		try:
			self.player.stop()
		except Exception:
			pass
		try:
			if self._gemini_thread is not None and self._gemini_thread.isRunning():
				self._gemini_thread.quit()
				self._gemini_thread.wait(3000)
				self._gemini_thread.deleteLater()
				self._gemini_thread = None
		except Exception:
			pass

	def info(self, msg: str) -> None:
		self.status.showMessage(msg, 8000)

	@Slot()
	def on_font_changed(self, font_name: str) -> None:
		"""Handle font family change"""
		self.apply_font_settings()

	@Slot()
	def on_font_size_changed(self, font_size: str) -> None:
		"""Handle font size change"""
		self.apply_font_settings()

	def apply_font_settings(self) -> None:
		"""Apply current font settings to all views"""
		font_name = self.font_combo.currentText()
		font_size = int(self.font_size_combo.currentText())
		
		# Create font
		from PySide6.QtGui import QFont
		font = QFont(font_name, font_size)
		
		# Apply to table view
		if hasattr(self, 'words_view'):
			self.words_view.setFont(font)
		
		# Apply to block view
		if hasattr(self, 'block_view'):
			self.block_view.set_font(font)
		
		# Apply to enhanced lyrics editor
		if hasattr(self, 'enhanced_lyrics_editor'):
			self.enhanced_lyrics_editor.set_font(font)
		
		self.info(f"Font changed to {font_name} {font_size}pt")
	
	@Slot()
	def on_word_duration_changed(self, value: int) -> None:
		"""Handle word duration slider change"""
		self.word_duration_label.setText(f"{value}.0s")
		
		# Sync duration to block view if it's visible
		if hasattr(self, 'block_view') and self.block_view.isVisible():
			# Update all block widgets with new duration
			for block_widget in self.block_view.block_widgets:
				if hasattr(block_widget, 'duration_seconds'):
					block_widget.duration_seconds = value
		
		# Sync duration to enhanced lyrics editor if it's visible
		if hasattr(self, 'enhanced_lyrics_editor') and self.enhanced_lyrics_editor.isVisible():
			# The enhanced editor uses the same duration for playback
			pass  # Duration is handled in the playback request

	@Slot()
	def on_view_mode_changed(self, view_mode: str) -> None:
		"""Handle view mode change"""
		if view_mode == "Table View":
			self.words_view.show()
			self.block_view.hide()
			self.enhanced_lyrics_editor.hide()
		elif view_mode == "Block View":
			self.words_view.hide()
			self.block_view.show()
			self.enhanced_lyrics_editor.hide()
			# Update block view with current data
		elif view_mode == "Enhanced Lyrics Editor":
			self.words_view.hide()
			self.block_view.hide()
			self.enhanced_lyrics_editor.show()
			# Update enhanced editor with current data
			if hasattr(self, 'words_model') and self.words_model.rows():
				self.enhanced_lyrics_editor.set_lyrics_data(self.words_model.rows())
			self.update_block_view()

	@Slot()
	def on_block_data_updated(self, updated_blocks) -> None:
		"""Handle block data updates"""
		# Update the main data structures with edited data
		updated_words = self.block_view.get_updated_words()
		updated_chords = self.block_view.get_updated_chords()
		
		# Update the table model
		self.words_model = WordsTableModel(updated_words)
		self.words_view.setModel(self.words_model)
		
		# Update detected chords
		self.detected_chords = updated_chords
		
		self.info("Block view changes saved")
	
	@Slot()
	def on_table_data_changed(self) -> None:
		"""Handle table view data changes (word edits)"""
		# When words are edited in table view, update block view
		if hasattr(self, 'block_view') and self.block_view.isVisible():
			self.update_block_view()
			self.info("Table view changes synced to block view")

	def update_block_view(self) -> None:
		"""Update block view with current data"""
		if not self.audio_path:
			return
		
		# Set audio path for playback
		self.block_view.set_audio_path(self.audio_path)
		
		# Get current words and chords
		words = self.words_model.rows()
		chords = self.detected_chords
		
		# Create blocks from data (Gemini data is now shown in table view)
		self.block_view.create_blocks_from_data(words, chords)
		
		# Update enhanced lyrics editor
		if hasattr(self, 'enhanced_lyrics_editor'):
			self.enhanced_lyrics_editor.set_lyrics_data(words)
	
	def on_enhanced_lyrics_changed(self, lyrics_text: str):
		"""Handle enhanced lyrics editor text changes"""
		# This could be used to sync changes back to the main model
		# For now, just log the change
		self.info("Enhanced lyrics editor text changed")
	
	def on_enhanced_play_audio_requested(self, start_time: float, duration: float):
		"""Handle audio playback request from enhanced lyrics editor"""
		if self.audio_path and os.path.exists(self.audio_path):
			self.player.load_audio(self.audio_path)
			self.player.play_segment(start_time, duration)

	def load_audio_from_path(self, path: str) -> None:
		"""Load audio from a specific file path (used for command line arguments)"""
		self.audio_path = path
		self.player.load(path)
		self.info(f"Loaded: {os.path.basename(path)}")

		# Check for pre-processed song data
		song_data_path = self.song_data_importer.find_song_data_file(path)
		if song_data_path:
			self.info(f"Found pre-processed data: {os.path.basename(song_data_path)}")
			self.imported_song_data = self.song_data_importer.import_song_data(song_data_path)

			if self.imported_song_data:
				# Load the imported data directly
				self.words_model = WordsTableModel(self.imported_song_data.words)
				self.words_view.setModel(self.words_model)

				# Convert imported chord data to DetectedChord format
				self.detected_chords = []
				for chord_data in self.imported_song_data.chords:
					from ..processing.chords import DetectedChord
					detected_chord = DetectedChord(
						name=chord_data.symbol,
						start=chord_data.start,
						end=chord_data.end,
						confidence=chord_data.confidence
					)
					self.detected_chords.append(detected_chord)

				# Annotate words with nearest-overlapping chord (same logic as run_chords)
				rows = self.words_model.rows()
				if rows and self.detected_chords:
					j = 0
					for row in rows:
						mid_t = 0.5 * (row.start + row.end)
						while j + 1 < len(self.detected_chords) and self.detected_chords[j].end < mid_t:
							j += 1
						ch = None
						if j < len(self.detected_chords) and self.detected_chords[j].start - 0.01 <= mid_t <= self.detected_chords[j].end + 0.01:
							ch = self.detected_chords[j].name
						row.chord = ch
					self.words_model.layoutChanged.emit()

				self.info(f"Imported {len(self.imported_song_data.words)} words and {len(self.detected_chords)} chords")
				return
			else:
				self.info("Failed to import song data, falling back to local processing")

		# Fall back to local processing if no pre-processed data found
		self.vocals_path = None
		self.instrumental_path = None
		self.detected_chords = []
		self.imported_song_data = None

		self.info("Stage: Separation")
		# Auto-run processing
		self.run_separation()
		self.info("Stage: Transcription")
		self.run_transcription()
		self.info("Stage: Chord Detection")
		self.run_chords()

	@Slot()
	def open_audio(self) -> None:
		# Create a custom file dialog that actually filters files
		from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
		from PySide6.QtCore import Qt
		
		# Create a custom dialog
		custom_dialog = QDialog(self)
		custom_dialog.setWindowTitle("Open Audio File - Only Audio Files Visible")
		custom_dialog.setModal(True)
		custom_dialog.resize(700, 500)
		
		layout = QVBoxLayout(custom_dialog)
		
		# Add a label
		label = QLabel("Select an audio file:")
		layout.addWidget(label)
		
		# Create a list widget to show only audio files
		file_list = QListWidget()
		layout.addWidget(file_list)
		
		# Scan directory for audio files
		audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.opus', '.aiff', '.alac'}
		current_dir = os.path.expanduser("~/Desktop")
		
		# Populate the list with audio files
		audio_files_found = False
		for filename in os.listdir(current_dir):
			if os.path.isfile(os.path.join(current_dir, filename)):
				ext = os.path.splitext(filename)[1].lower()
				if ext in audio_extensions:
					file_list.addItem(filename)
					audio_files_found = True
		
		# If no audio files found, show message
		if not audio_files_found:
			label.setText("No audio files found in Desktop.\nSupported formats: WAV, MP3, FLAC, M4A, AAC, OGG, WMA, OPUS, AIFF, ALAC")
			open_button.setEnabled(False)
		else:
			# Show count of audio files found
			label.setText(f"Found {file_list.count()} audio files in Desktop. Select one to open:")
		
		# Add directory selection
		dir_layout = QHBoxLayout()
		dir_label = QLabel("Directory:")
		dir_path_label = QLabel(current_dir)
		dir_path_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
		change_dir_button = QPushButton("Change Directory")
		dir_layout.addWidget(dir_label)
		dir_layout.addWidget(dir_path_label, 1)
		dir_layout.addWidget(change_dir_button)
		layout.addLayout(dir_layout)
		
		# Add buttons
		button_layout = QHBoxLayout()
		open_button = QPushButton("Open")
		cancel_button = QPushButton("Cancel")
		button_layout.addWidget(open_button)
		button_layout.addWidget(cancel_button)
		layout.addLayout(button_layout)
		
		# Connect signals
		open_button.clicked.connect(custom_dialog.accept)
		cancel_button.clicked.connect(custom_dialog.reject)
		
		# Directory change functionality
		dir_vars = {'current_dir': current_dir}
		def change_directory():
			from PySide6.QtWidgets import QFileDialog
			new_dir = QFileDialog.getExistingDirectory(custom_dialog, "Select Directory", dir_vars['current_dir'])
			if new_dir:
				# Update the directory display
				dir_path_label.setText(new_dir)
				# Clear and repopulate the file list
				file_list.clear()
				audio_files_found = False
				for filename in os.listdir(new_dir):
					if os.path.isfile(os.path.join(new_dir, filename)):
						ext = os.path.splitext(filename)[1].lower()
						if ext in audio_extensions:
							file_list.addItem(filename)
							audio_files_found = True
				
				# Update the label
				if not audio_files_found:
					label.setText(f"No audio files found in {os.path.basename(new_dir)}.\nSupported formats: WAV, MP3, FLAC, M4A, AAC, OGG, WMA, OPUS, AIFF, ALAC")
					open_button.setEnabled(False)
				else:
					label.setText(f"Found {file_list.count()} audio files in {os.path.basename(new_dir)}. Select one to open:")
					open_button.setEnabled(False)  # Will be enabled when selection changes
				
				# Update current_dir for the final path construction
				dir_vars['current_dir'] = new_dir
		
		change_dir_button.clicked.connect(change_directory)
		
		# Enable/disable open button based on selection
		open_button.setEnabled(False)
		file_list.itemSelectionChanged.connect(lambda: open_button.setEnabled(len(file_list.selectedItems()) > 0))
		
		# Allow double-click to open
		file_list.itemDoubleClicked.connect(custom_dialog.accept)
		
		# Show the custom dialog
		if custom_dialog.exec() == QDialog.Accepted:
			selected_items = file_list.selectedItems()
			if selected_items:
				path = os.path.join(dir_vars['current_dir'], selected_items[0].text())
			else:
				return
		else:
			return
		

		
		self.audio_path = path
		self.player.load(path)
		self.info(f"Loaded: {os.path.basename(path)}")
		
		# Set audio path for all views
		if hasattr(self, 'block_view'):
			self.block_view.set_audio_path(path)
		if hasattr(self, 'enhanced_lyrics_editor'):
			self.enhanced_lyrics_editor.set_audio_path(path)
		
		# Check for pre-processed song data
		song_data_path = self.song_data_importer.find_song_data_file(path)
		if song_data_path:
			self.info(f"Found pre-processed data: {os.path.basename(song_data_path)}")
			self.imported_song_data = self.song_data_importer.import_song_data(song_data_path)
			
			if self.imported_song_data:
				# Load the imported data directly
				self.words_model = WordsTableModel(self.imported_song_data.words)
				self.words_view.setModel(self.words_model)
				
				# Convert imported chord data to DetectedChord format
				self.detected_chords = []
				for chord_data in self.imported_song_data.chords:
					from ..processing.chords import DetectedChord
					detected_chord = DetectedChord(
						name=chord_data.symbol,
						start=chord_data.start,
						end=chord_data.end,
						confidence=chord_data.confidence
					)
					self.detected_chords.append(detected_chord)
				
				# Annotate words with nearest-overlapping chord (same logic as run_chords)
				rows = self.words_model.rows()
				if rows and self.detected_chords:
					j = 0
					for row in rows:
						mid_t = 0.5 * (row.start + row.end)
						while j + 1 < len(self.detected_chords) and self.detected_chords[j].end < mid_t:
							j += 1
						ch = None
						if j < len(self.detected_chords) and self.detected_chords[j].start - 0.01 <= mid_t <= self.detected_chords[j].end + 0.01:
							ch = self.detected_chords[j].name
						row.chord = ch
					self.words_model.layoutChanged.emit()
				
				self.info(f"Imported {len(self.imported_song_data.words)} words and {len(self.detected_chords)} chords")
				return
			else:
				self.info("Failed to import song data, falling back to local processing")
		
		# Fall back to local processing if no pre-processed data found
		self.vocals_path = None
		self.instrumental_path = None
		self.detected_chords = []
		self.imported_song_data = None
		
		self.info("Stage: Separation")
		# Auto-run processing
		self.run_separation()
		self.info("Stage: Transcription")
		self.run_transcription()
		self.info("Stage: Chord Detection")
		self.run_chords()

	@Slot()
	def run_transcription(self) -> None:
		if not self.audio_path:
			self.info("Load an audio file first")
			return
		model = self.model_combo.currentText()
		self.info(f"Transcribing with {model}...")
		use_path = self.vocals_path or self.audio_path
		words: List[Word] = self.transcriber.transcribe(use_path, model_size=model)
		rows = [WordRow(w.text, w.start, w.end, w.confidence or 0.0) for w in words]
		self.words_model = WordsTableModel(rows)
		self.words_view.setModel(self.words_model)
		self.info(f"Transcribed {len(rows)} words")
		
		# Update block view if it's currently visible
		if self.view_mode_combo.currentText() == "Block View":
			self.update_block_view()
		
		# Update enhanced lyrics editor if it's currently visible
		if self.view_mode_combo.currentText() == "Enhanced Lyrics Editor":
			if hasattr(self, 'enhanced_lyrics_editor'):
				self.enhanced_lyrics_editor.set_lyrics_data(rows)

	@Slot()
	def run_chords(self) -> None:
		if not self.audio_path:
			self.info("Load an audio file first")
			return
		self.info("Detecting chords (major/minor)...")
		use_path = self.instrumental_path or self.audio_path
		self.detected_chords = self.chord_detector.detect(use_path)
		self.info(f"Chord detection complete: {len(self.detected_chords)} segments")
		# Annotate words with nearest-overlapping chord
		rows = self.words_model.rows()
		if not rows or not self.detected_chords:
			return
		j = 0
		for row in rows:
			mid_t = 0.5 * (row.start + row.end)
			while j + 1 < len(self.detected_chords) and self.detected_chords[j].end < mid_t:
				j += 1
			ch = None
			if self.detected_chords[j].start - 0.01 <= mid_t <= self.detected_chords[j].end + 0.01:
				ch = self.detected_chords[j].name
			row.chord = ch
		self.words_model.layoutChanged.emit()
		
		# Update block view if it's currently visible
		if self.view_mode_combo.currentText() == "Block View":
			self.update_block_view()

	@Slot()
	def run_separation(self) -> None:
		if not self.audio_path:
			self.info("Load an audio file first")
			return
		if self.vocals_path and self.instrumental_path and os.path.exists(self.vocals_path) and os.path.exists(self.instrumental_path):
			self.info("Stems already separated; skipping")
			return
		self.info("Separating stems (Demucs)...")
		voc, inst = separate_vocals_instrumental(self.audio_path)
		self.vocals_path = voc
		self.instrumental_path = inst
		if voc and inst:
			self.info("Separation complete; using stems for processing")
		else:
			self.info("Separation unavailable; using original mix")

	@Slot()
	def on_row_double_clicked(self, index: QModelIndex) -> None:
		if not index.isValid():
			return
		
		row = self.words_model.rows()[index.row()]
		
		# Get duration from the word duration slider
		duration_seconds = self.word_duration_slider.value()
		
		# Calculate center point of the word
		word_center = (row.start + row.end) / 2
		
		# Calculate start and end times centered on the word
		half_duration = duration_seconds / 2
		start = max(0.0, word_center - half_duration)
		end = word_center + half_duration
		
		self.player.play_segment(start, end)

	@Slot()
	def generate_gemini_alt(self) -> None:
		if not self.words_model.rows():
			self.info("Transcribe first")
			return
		if not self.gemini.ensure_api_key():
			self.info("Set GEMINI_API_KEY in environment to enable alt lyrics")
			return
		self.info("Requesting Gemini alternative lyrics...")
		self.gemini_act.setEnabled(False)
		QApplication.setOverrideCursor(Qt.BusyCursor)

		class GeminiWorker(QThread):
			finished_ok = Signal(list, list)
			failed = Signal(str)

			def __init__(self, client: GeminiClient, text: str, model_name: str, words_with_alternatives: List = None) -> None:
				super().__init__()
				self.client = client
				self.text = text
				self.model_name = model_name
				self.words_with_alternatives = words_with_alternatives

			def run(self) -> None:
				try:
					self.client.model_name = self.model_name
					alts = self.client.rewrite_lyrics(self.text, self.words_with_alternatives)
					if not alts:
						msg = "No alternative returned"
						if getattr(self.client, "last_debug", ""):
							msg += ": " + self.client.last_debug
						self.failed.emit(msg)
						return
					alt_chords = self.client.infer_chords(" ".join(a.text for a in alts))
					self.finished_ok.emit(alts, alt_chords)
				except Exception as e:
					self.failed.emit(str(e))

		text = " ".join(r.text for r in self.words_model.rows())
		words_with_alternatives = self.words_model.rows()
		worker = GeminiWorker(self.gemini, text, self.gemini_model_combo.currentText(), words_with_alternatives)
		self._gemini_thread = worker
		
		# Show Gemini columns when processing starts
		self.words_model.set_show_gemini_columns(True)

		def on_done(alts, alt_chords) -> None:
			for i, row in enumerate(self.words_model.rows()):
				if i < len(alts):
					row.gemini_text = alts[i].text
			for i, row in enumerate(self.words_model.rows()):
				if i < len(alt_chords):
					row.gemini_chord = alt_chords[i].text
			self.words_model.layoutChanged.emit()
			self.info("Gemini alternative columns populated")
			self.gemini_act.setEnabled(True)
			
			# Update block view if it's currently visible
			if self.view_mode_combo.currentText() == "Block View":
				self.update_block_view()
			QApplication.restoreOverrideCursor()
			if self._gemini_thread is not None:
				self._gemini_thread.deleteLater()
				self._gemini_thread = None

		def on_fail(msg: str) -> None:
			self.info(msg)
			self.gemini_act.setEnabled(True)
			QApplication.restoreOverrideCursor()
			if self._gemini_thread is not None:
				self._gemini_thread.deleteLater()
				self._gemini_thread = None

		worker.finished_ok.connect(on_done)
		worker.failed.connect(on_fail)
		worker.start()

	@Slot()
	def generate_gemini_from_audio(self) -> None:
		if not self.audio_path:
			self.info("Load an audio file first")
			return
		if not self.gemini.ensure_api_key():
			self.info("Set GEMINI_API_KEY to enable cloud transcription")
			return
		self.info("Gemini audio analysis...")
		if hasattr(self, "gemini_audio_act"):
			self.gemini_audio_act.setEnabled(False)
		QApplication.setOverrideCursor(Qt.BusyCursor)
		class GeminiAudioWorker(QThread):
			finished_ok = Signal(list, list)
			failed = Signal(str)
			def __init__(self, client: GeminiClient, audio_path: str, model_name: str, chunk_seconds: int, sleep_between: int) -> None:
				super().__init__()
				self.client = client
				self.path = audio_path
				self.model = model_name
				self.chunk_seconds = chunk_seconds
				self.sleep_between = sleep_between
			def run(self) -> None:
				try:
					self.client.model_name = self.model
					alts, chords = self.client.analyze_audio_alt_chunked(
						self.path,
						chunk_seconds=self.chunk_seconds,
						sleep_between=self.sleep_between,
					)
					if not alts:
						msg = "No alternative returned"
						if getattr(self.client, "last_debug", ""):
							msg += ": " + self.client.last_debug
						self.failed.emit(msg)
						return
					self.finished_ok.emit(alts, chords)
				except Exception as e:
					self.failed.emit(str(e))
		worker = GeminiAudioWorker(
			self.gemini,
			self.audio_path,
			self.gemini_model_combo.currentText(),
			self.gemini_chunk_seconds,
			self.gemini_sleep_between,
		)
		self._gemini_thread = worker
		def on_done(alts, chords) -> None:
			rows = self.words_model.rows()
			# Time-based alignment: find nearest local word for each Gemini result
			if not rows:
				# If no local rows, create from Gemini data
				for a in alts:
					rows.append(WordRow(a.text, a.start, a.end, 0.0))
			else:
				# Clear previous alt data
				for row in rows:
					row.alt_text = None
					row.alt_chord = None
					row.alt_start = None
					row.alt_end = None
				# Align Gemini words to nearest local words by time
				for i, alt in enumerate(alts):
					alt_mid = 0.5 * (alt.start + alt.end)
					best_idx = -1
					best_dist = float('inf')
					for j, row in enumerate(rows):
						row_mid = 0.5 * (row.start + row.end)
						dist = abs(alt_mid - row_mid)
						if dist < best_dist:
							best_dist = dist
							best_idx = j
					if best_idx >= 0:
						rows[best_idx].alt_text = alt.text
						rows[best_idx].alt_start = alt.start
						rows[best_idx].alt_end = alt.end
				# Align Gemini chords to nearest local words by time
				for i, chord in enumerate(chords):
					chord_mid = 0.5 * (chord.start + chord.end)
					best_idx = -1
					best_dist = float('inf')
					for j, row in enumerate(rows):
						row_mid = 0.5 * (row.start + row.end)
						dist = abs(chord_mid - row_mid)
						if dist < best_dist:
							best_dist = dist
							best_idx = j
					if best_idx >= 0:
						rows[best_idx].alt_chord = chord.symbol
			self.words_model.layoutChanged.emit()
			self.info("Gemini audio alternatives populated")
			
			# Update block view if it's currently visible
			if self.view_mode_combo.currentText() == "Block View":
				self.update_block_view()
			if hasattr(self, "gemini_audio_act"):
				self.gemini_audio_act.setEnabled(True)
			QApplication.restoreOverrideCursor()
			if self._gemini_thread is not None:
				self._gemini_thread.deleteLater()
				self._gemini_thread = None
		def on_fail(msg: str) -> None:
			self.info(msg)
			if hasattr(self, "gemini_audio_act"):
				self.gemini_audio_act.setEnabled(True)
			QApplication.restoreOverrideCursor()
			if self._gemini_thread is not None:
				self._gemini_thread.deleteLater()
				self._gemini_thread = None
		worker.finished_ok.connect(on_done)
		worker.failed.connect(on_fail)
		worker.start()

	def open_cloud_settings(self) -> None:
		dlg = QDialog(self)
		dlg.setWindowTitle("Cloud Processing Settings")
		v = QVBoxLayout(dlg)
		v.addWidget(QLabel("Chunk seconds"))
		slider_chunk = QSlider(Qt.Horizontal)
		slider_chunk.setMinimum(15)
		slider_chunk.setMaximum(180)
		slider_chunk.setValue(self.gemini_chunk_seconds)
		v.addWidget(slider_chunk)
		v.addWidget(QLabel("Sleep between (s)"))
		slider_sleep = QSlider(Qt.Horizontal)
		slider_sleep.setMinimum(0)
		slider_sleep.setMaximum(300)
		slider_sleep.setValue(self.gemini_sleep_between)
		v.addWidget(slider_sleep)
		buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		v.addWidget(buttons)
		def accept():
			self.gemini_chunk_seconds = slider_chunk.value()
			self.gemini_sleep_between = slider_sleep.value()
			dlg.accept()
		buttons.accepted.connect(accept)
		buttons.rejected.connect(dlg.reject)
		dlg.exec()

	def closeEvent(self, event) -> None:  # type: ignore[override]
		try:
			if self._gemini_thread is not None and self._gemini_thread.isRunning():
				self.info("Waiting for background tasks to finish...")
				# best effort: wait longer; if still running, terminate as last resort
				self._gemini_thread.wait(300000)
				if self._gemini_thread.isRunning():
					self._gemini_thread.terminate()
					self._gemini_thread.wait(5000)
		finally:
			return super().closeEvent(event)

	@Slot()
	def export_ccli_text(self) -> None:
		if not self.words_model.rows():
			self.info("Nothing to export")
			return
		path, _ = QFileDialog.getSaveFileName(self, "Export CCLI", os.getcwd(), "ChordPro (*.cho *.chordpro *.pro *.crd);;Text (*.txt)")
		if not path:
			return
		export_ccli(path, self.words_model.rows())
		self.info("Exported CCLI text")

	@Slot()
	def export_midi(self) -> None:
		if not self.words_model.rows():
			self.info("Nothing to export")
			return
		path, _ = QFileDialog.getSaveFileName(self, "Export MIDI", os.getcwd(), "MIDI Files (*.mid)")
		if not path:
			return
		
		# Get current data (use block view data if available and edited)
		words = self.words_model.rows()
		chords = self.detected_chords
		
		# If block view is active and has been edited, use its data
		if (self.view_mode_combo.currentText() == "Block View" and 
			self.block_view.save_btn.isEnabled()):
			words = self.block_view.get_updated_words()
			chords = self.block_view.get_updated_chords()
		
		# Pass melody if available from last Gemini call
		melody = getattr(self.gemini, 'last_notes', None)
		export_midi(path, words, chords, melody)
		self.info("Exported MIDI")

	@Slot()
	def export_song_data(self) -> None:
		if not self.words_model.rows():
			self.info("Nothing to export")
			return
		
		# Suggest filename based on audio file
		suggested_name = ""
		if self.audio_path:
			audio_path = Path(self.audio_path)
			suggested_name = str(audio_path.with_suffix('.song_data'))
		
		path, _ = QFileDialog.getSaveFileName(
			self, 
			"Export Song Data", 
			suggested_name,
			"Song Data Files (*.song_data *.json);;JSON Files (*.json)"
		)
		if not path:
			return
		
		try:
			# Create SongData object from current state
			from datetime import datetime
			
			# Convert detected chords to ChordData format
			chord_data_list = []
			for chord in self.detected_chords:
				from ..models.song_data_importer import ChordData
				chord_data = ChordData(
					symbol=chord.name,
					root=chord.name[0] if chord.name else '',
					quality=chord.name[1:] if len(chord.name) > 1 else 'maj',
					bass=None,
					start=chord.start,
					end=chord.end,
					confidence=chord.confidence
				)
				chord_data_list.append(chord_data)
			
			# Create metadata
			metadata = {
				"version": "2.0.0",
				"created_at": datetime.now().isoformat(),
				"source_audio": self.audio_path or "",
				"processing_tool": "Song Editor 2",
				"confidence_threshold": 0.7
			}
			
			# Create SongData object
			song_data = SongData(
				metadata=metadata,
				words=self.words_model.rows(),
				chords=chord_data_list,
				notes=[],  # Could be populated from Gemini notes if available
				segments=[]  # Could be populated from segment detection if available
			)
			
			# Export using the importer's export function
			if self.song_data_importer.export_song_data(song_data, path):
				self.info(f"Exported song data to {os.path.basename(path)}")
			else:
				self.info("Failed to export song data")
				
		except Exception as e:
			self.info(f"Error exporting song data: {e}")
	
	def _is_audio_file_supported(self, file_path: str) -> bool:
		"""Check if the audio file format is supported by our processing libraries"""
		import soundfile as sf
		
		# Get file extension
		file_ext = os.path.splitext(file_path)[1].lower()
		
		# Define supported extensions
		supported_extensions = {
			'.wav', '.mp3', '.flac', '.m4a', '.aac', 
			'.ogg', '.wma', '.opus', '.aiff', '.alac'
		}
		
		# Check if extension is supported
		if file_ext not in supported_extensions:
			return False
		
		# Try to read the file header to validate it's actually an audio file
		try:
			with sf.SoundFile(file_path) as audio_file:
				# If we can open it with soundfile, it's likely supported
				return True
		except Exception:
			# If soundfile can't read it, it might still be supported by other libraries
			# but we'll warn the user
			return False
	
	@Slot()
	def show_supported_formats(self) -> None:
		"""Show information about supported audio formats"""
		formats_info = """
<b>Supported Audio Formats:</b><br><br>

<u>Primary Formats (Best Compatibility):</u><br>
• <b>WAV</b> (*.wav) - Uncompressed, highest quality<br>
• <b>MP3</b> (*.mp3) - Compressed, widely supported<br>
• <b>FLAC</b> (*.flac) - Lossless compression<br>
• <b>M4A/AAC</b> (*.m4a, *.aac) - Apple/Android standard<br><br>

<u>Additional Formats:</u><br>
• <b>OGG Vorbis</b> (*.ogg) - Open source compressed<br>
• <b>WMA</b> (*.wma) - Windows Media Audio<br>
• <b>Opus</b> (*.opus) - Modern low-latency codec<br>
• <b>AIFF</b> (*.aiff) - Apple uncompressed<br>
• <b>ALAC</b> (*.alac) - Apple lossless compression<br><br>

<u>Recommendations:</u><br>
• Use <b>WAV</b> for best processing quality<br>
• Use <b>MP3</b> for smaller file sizes<br>
• Use <b>FLAC</b> for lossless compression<br>
• Convert unsupported formats to WAV or MP3<br><br>

<u>File Size Guidelines:</u><br>
• WAV: ~10-50 MB per minute (depending on quality)<br>
• MP3: ~1-5 MB per minute (depending on bitrate)<br>
• FLAC: ~5-25 MB per minute (depending on complexity)
		"""
		
		QMessageBox.information(
			self,
			"Supported Audio Formats",
			formats_info
		)


