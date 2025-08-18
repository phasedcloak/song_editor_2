# Song Data Format Documentation

## Overview

The Song Editor 2 application now supports importing and exporting pre-processed song data in a standardized JSON format. This allows you to:

1. **Skip local processing** by providing pre-processed transcription data
2. **Export processed data** for use in other applications
3. **Share song data** between different tools and workflows

## File Format

### File Extensions
The application looks for song data files with these extensions (in order of preference):
- `.song_data` (recommended)
- `.song_data.json`
- `.json`

### Naming Convention
Song data files should have the same basename as the audio file:
```
song.wav          → song.song_data
my_track.mp3      → my_track.song_data
audio.flac        → audio.song_data
```

## Schema

The song data format follows a JSON schema defined in `song_data_schema.json`. Here's the structure:

### Top-Level Structure
```json
{
  "metadata": { ... },
  "words": [ ... ],
  "chords": [ ... ],
  "notes": [ ... ],
  "segments": [ ... ]
}
```

### Required Fields
- `metadata`: Information about the transcription
- `words`: Array of transcribed words with timing and chords

### Optional Fields
- `chords`: Array of detected chords with timing
- `notes`: Array of detected melody notes
- `segments`: Array of song segments (verse, chorus, etc.)

## Data Types

### Metadata
```json
{
  "version": "2.0.0",
  "created_at": "2024-08-15T14:30:00Z",
  "source_audio": "/path/to/song.wav",
  "processing_tool": "Song Editor 2",
  "confidence_threshold": 0.7
}
```

### Words
Each word object contains:
```json
{
  "text": "Hello",
  "start": 0.5,
  "end": 0.8,
  "confidence": 0.95,
  "chord": {
    "symbol": "C",
    "root": "C",
    "quality": "maj",
    "bass": null,
    "confidence": 0.88
  }
}
```

### Chords
```json
{
  "symbol": "Cmaj7",
  "root": "C",
  "quality": "maj7",
  "bass": null,
  "start": 0.0,
  "end": 0.8,
  "confidence": 0.88
}
```

### Notes
```json
{
  "pitch_midi": 60,
  "pitch_name": "C4",
  "start": 0.5,
  "end": 0.8,
  "velocity": 80,
  "confidence": 0.85
}
```

### Segments
```json
{
  "type": "verse",
  "label": "Verse 1",
  "start": 0.5,
  "end": 1.2,
  "confidence": 0.92
}
```

## Usage Examples

### Creating Song Data for External Processing

1. **Process audio in your preferred tool** (e.g., Whisper, Chordify, etc.)
2. **Format the output** according to the schema
3. **Save as `.song_data` file** with the same basename as the audio
4. **Load in Song Editor 2** - it will automatically detect and import the data

### Example: Whisper + Chord Detection Pipeline

```python
import whisper
import json
from datetime import datetime

# Process audio with Whisper
model = whisper.load_model("base")
result = model.transcribe("song.wav")

# Process with chord detection (example)
chord_results = detect_chords("song.wav")

# Create song data structure
song_data = {
    "metadata": {
        "version": "2.0.0",
        "created_at": datetime.now().isoformat(),
        "source_audio": "song.wav",
        "processing_tool": "Whisper + Custom Chord Detection",
        "confidence_threshold": 0.7
    },
    "words": [],
    "chords": []
}

# Convert Whisper segments to words
for segment in result["segments"]:
    for word in segment["words"]:
        word_data = {
            "text": word["word"],
            "start": word["start"],
            "end": word["end"],
            "confidence": word.get("confidence", 0.8),
            "chord": None  # Will be filled by chord detection
        }
        song_data["words"].append(word_data)

# Add chord data
for chord in chord_results:
    chord_data = {
        "symbol": chord["symbol"],
        "root": chord["root"],
        "quality": chord["quality"],
        "bass": chord.get("bass"),
        "start": chord["start"],
        "end": chord["end"],
        "confidence": chord.get("confidence", 0.8)
    }
    song_data["chords"].append(chord_data)

# Save to file
with open("song.song_data", "w") as f:
    json.dump(song_data, f, indent=2)
```

### Example: Using with Song Editor 2

1. **Place your `.song_data` file** next to the audio file
2. **Open the audio file** in Song Editor 2
3. **The application will automatically detect** and import the pre-processed data
4. **Skip local processing** - all transcription and chord data is loaded immediately

## Integration with Song Editor 2

### Automatic Detection
When you open an audio file, Song Editor 2 automatically:
1. Looks for a `.song_data` file with the same basename
2. Validates the data format
3. Imports words, chords, and other data
4. Skips local processing if valid data is found

### Manual Export
You can export the current song data:
1. Process audio normally in Song Editor 2
2. Click "Export Song Data" in the toolbar
3. Choose a filename and location
4. The data is saved in the standardized format

### Fallback Behavior
If no `.song_data` file is found or if the data is invalid:
1. Song Editor 2 falls back to local processing
2. Audio separation, transcription, and chord detection run normally
3. No error is shown - the application works as before

## Validation

The application validates song data files using these criteria:

### Required Fields
- `metadata.version`: Must be a valid version string
- `metadata.created_at`: Must be a valid ISO datetime
- `metadata.source_audio`: Must be a string
- `words`: Must be a non-empty array

### Word Validation
Each word must have:
- `text`: Non-empty string
- `start`: Numeric value ≥ 0
- `end`: Numeric value ≥ 0
- `confidence`: Numeric value between 0 and 1

### Chord Validation
Each chord must have:
- `symbol`: Non-empty string
- `root`: Non-empty string
- `quality`: Non-empty string
- `start`: Numeric value ≥ 0
- `end`: Numeric value ≥ 0

## Best Practices

### File Organization
```
project/
├── song.wav
├── song.song_data          # Pre-processed data
├── song_alt.song_data      # Alternative version
└── processed/
    ├── song_vocals.wav
    └── song_instrumental.wav
```

### Data Quality
- Use confidence scores to filter low-quality transcriptions
- Ensure timing accuracy for proper synchronization
- Include chord information when available
- Add metadata for traceability

### Performance
- Large song data files load faster than processing audio
- Pre-processed data reduces CPU usage
- Enable parallel processing workflows

## Error Handling

### Common Issues
1. **Missing file**: Application falls back to local processing
2. **Invalid JSON**: Error message shown, fallback to local processing
3. **Schema mismatch**: Validation errors, fallback to local processing
4. **Timing issues**: Data loaded but may need adjustment

### Debugging
- Check the application status bar for import messages
- Verify JSON syntax with a validator
- Ensure file naming matches the audio file
- Test with the provided example files

## Future Extensions

The schema is designed to be extensible:
- Additional metadata fields
- More detailed chord information
- Tempo and key detection
- Multiple language support
- Custom annotations

## Support

For questions or issues:
1. Check the schema validation
2. Review the example files
3. Test with the provided test script
4. Consult the application documentation
