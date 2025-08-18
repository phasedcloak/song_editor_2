## Song Editor 2

A desktop song editor for processing audio files into editable, time-aligned lyrics and chords with export to CCLI-style text and multitrack MIDI. Built with Python and Qt.

### Features
- Local transcription (Whisper via faster-whisper) with word-level timestamps and confidence
- Optional source separation (vocals/instrumental) when Demucs is available
- Chord detection from instrumental using chroma templates
- Interactive UI:
  - Double-click a word to play that audio segment
  - Edit words inline; colors indicate confidence (red→yellow→green)
  - Optional Gemini-based alternative lyrics suggestion
- Export:
  - CCLI-like chord/lyrics text (ChordPro-compatible)
  - Multitrack MIDI with lyrics meta events and chord blocks

### Requirements
- Python 3.10+
- macOS, Windows, or Linux
- For audio playback: system PortAudio (installed automatically by `sounddevice` on macOS via wheels)
- Optional heavy models:
  - Demucs (source separation) [optional]
  - PyTorch (Demucs dependency) [optional]

### Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional extras:

```bash
# Demucs separation (CPU works, GPU faster). Torch may need platform-specific wheels.
pip install demucs torch
```

### Run

```bash
python -m song_editor.app
```

### Gemini (Optional)
To enable cloud-based alternative lyric suggestions, set an API key in your environment:

```bash
export GEMINI_API_KEY=your_key_here  # Windows: set GEMINI_API_KEY=your_key_here
```

In the app, use Cloud → Generate Gemini Alternative. This does not upload audio; it rewrites the local transcript text.

### Notes on Models
- Whisper (faster-whisper) runs locally on CPU with CTranslate2; choose model size in Settings → Transcription.
- Separation is optional. If unavailable, transcription runs on the full mix; chord detection uses the full mix as a fallback.

### Exports
- CCLI text is exported as a ChordPro-compatible file with inline chords like `[C]word`.
- MIDI export produces:
  - Track 0: Tempo and markers
  - Track 1: Lyrics meta events at word times
  - Track 2: Chord block notes per detected chord

### Disclaimer
This project depends on third-party ML models. Heavy model downloads may occur on first use. For best accuracy, use separation prior to chord detection.


