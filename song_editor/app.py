import sys
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> int:
	# Best-effort: use spawn to avoid semaphore leaks from forked workers (Demucs/torch)
	try:
		import multiprocessing as _mp
		_mp.set_start_method("spawn", force=True)
	except Exception:
		pass
	# Best-effort: clear resource tracker semaphores on startup
	try:
		from multiprocessing import resource_tracker as _rt  # type: ignore
		if hasattr(_rt, "_resource_tracker"):
			_rt._resource_tracker._cleanup()  # type: ignore[attr-defined]
	except Exception:
		pass
	app = QApplication(sys.argv)
	app.setApplicationName("Song Editor 2")
	
	# Parse command line arguments for audio file
	audio_file_arg = None
	if len(sys.argv) > 1:
		# Check for help
		if sys.argv[1] in ['-h', '--help', '-?']:
			print("Song Editor 2 - Audio Processing Tool")
			print("")
			print("Usage:")
			print("  song-editor                    # Open without audio file")
			print("  song-editor <audio_file>      # Open with specific audio file")
			print("")
			print("Examples:")
			print("  song-editor ~/Desktop/song.wav")
			print("  song-editor /path/to/audio.mp3")
			print("")
			print("Supported audio formats: WAV, MP3, FLAC, M4A, AAC, OGG, WMA, OPUS, AIFF, ALAC")
			return 0
		
		audio_file_arg = sys.argv[1]
		# Validate that the file exists and is an audio file
		import os
		audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.opus', '.aiff', '.alac'}
		if not os.path.isfile(audio_file_arg):
			print(f"Error: File '{audio_file_arg}' does not exist.")
			return 1
		ext = os.path.splitext(audio_file_arg)[1].lower()
		if ext not in audio_extensions:
			print(f"Error: File '{audio_file_arg}' is not a supported audio format.")
			print(f"Supported formats: {', '.join(audio_extensions)}")
			return 1
	
	window = MainWindow()
	
	# If audio file was provided via command line, load it automatically
	if audio_file_arg:
		window.load_audio_from_path(audio_file_arg)
	
	# Cleanup on quit
	def _on_quit() -> None:
		try:
			window.prepare_shutdown()
		except Exception:
			pass
	app.aboutToQuit.connect(_on_quit)
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())


