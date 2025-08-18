# Block View Documentation

## Overview

The Block View is an optional display mode in Song Editor 2 that shows song data in 20-second blocks, making it easier to analyze and edit lyrics and chords. This view is particularly useful for comparing local transcription results with Gemini-generated alternatives.

## Features

### 1. **20-Second Block Display**
- Song data is divided into 20-second segments
- Each block shows time range (e.g., "0.0s - 20.0s")
- Blocks are displayed vertically for easy scrolling

### 2. **Four-Line Format per Block**
Each block displays:
1. **Local Chord**: Chord detected by local processing
2. **Gemini Chord**: Chord suggested by Gemini AI
3. **Local Lyrics**: Lyrics transcribed by local processing
4. **Gemini Lyrics**: Lyrics suggested by Gemini AI

### 3. **Editable Fields**
- All chord and lyrics fields are editable
- Changes are tracked and can be saved
- "Save Changes" button becomes enabled when edits are made

### 4. **Audio Playback**
- Play button (▶) next to each lyrics section
- Plays 5 seconds of audio starting from the block's time
- Helps verify transcription accuracy during editing

### 5. **View Mode Selection**
- Dropdown menu to switch between "Table View" and "Block View"
- Seamless transition between views
- Data is automatically synchronized between views

## Usage

### Switching to Block View
1. Open an audio file in Song Editor 2
2. Wait for transcription and chord detection to complete
3. Select "Block View" from the "View" dropdown
4. The interface switches to show 20-second blocks

### Editing Data
1. **Edit Chords**: Click in any chord field and type new chord symbols
2. **Edit Lyrics**: Click in any lyrics field and modify the text
3. **Save Changes**: Click "Save Changes" to apply edits
4. **Audio Verification**: Click play buttons to hear the audio segment

### Audio Playback
- Click the ▶ button next to any lyrics section
- Audio plays for 5 seconds starting from that block's time
- Useful for verifying transcription accuracy
- Only one audio segment plays at a time

### Data Synchronization
- Changes made in Block View are reflected in Table View
- Export functions use the updated data
- MIDI export includes edited chords and lyrics

## Interface Layout

### Block Structure
```
┌─────────────────────────────────────────────────────────┐
│ 0.0s - 20.0s                                            │
├─────────────────────────────────────────────────────────┤
│ Local Chord:  [C        ]                               │
│ Gemini Chord: [Cmaj7    ]                               │
│ Local Lyrics: [Hello world how are you today...] [▶]   │
│ Gemini Lyrics:[Greetings world how are you today...] [▶]│
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ 20.0s - 40.0s                                           │
├─────────────────────────────────────────────────────────┤
│ Local Chord:  [Am       ]                               │
│ Gemini Chord: [Amin     ]                               │
│ Local Lyrics: [I hope you are doing well...] [▶]       │
│ Gemini Lyrics:[I trust you are doing well...] [▶]      │
└─────────────────────────────────────────────────────────┘
```

### Controls
- **View Dropdown**: Switch between Table View and Block View
- **Save Changes**: Apply edits to the main data structure
- **Play Buttons**: Play audio segments for verification

## Data Flow

### From Table View to Block View
1. Table View data is automatically converted to blocks
2. Words are grouped by time into 20-second segments
3. Chords are assigned to blocks based on timing overlap
4. Gemini alternatives are included if available

### From Block View to Table View
1. Edited data is converted back to WordRow objects
2. Chord changes are applied to DetectedChord objects
3. Table View is updated to reflect changes
4. Export functions use the updated data

### Export Integration
- MIDI export uses edited data from Block View
- CCLI export includes updated lyrics and chords
- Song data export preserves all edits

## Best Practices

### Editing Workflow
1. **Review**: Use Table View for initial review of transcription
2. **Switch**: Switch to Block View for detailed editing
3. **Verify**: Use audio playback to verify transcription accuracy
4. **Edit**: Make corrections to chords and lyrics
5. **Save**: Save changes to apply them to the main data
6. **Export**: Export the corrected data

### Audio Playback Tips
- Use playback to verify difficult-to-transcribe words
- Check timing accuracy of chord changes
- Verify pronunciation and context
- Use playback to identify transcription errors

### Data Consistency
- Always save changes before switching views
- Verify that edits are applied correctly
- Check that timing information is preserved
- Ensure chord symbols are in standard format

## Technical Details

### Block Creation Algorithm
1. Calculate total song duration
2. Divide into 20-second segments
3. Assign words to blocks based on timing
4. Assign chords to blocks based on overlap
5. Include Gemini alternatives if available

### Data Structures
- **BlockData**: Contains all data for a 20-second block
- **EditableChordLine**: Single-line chord editor
- **EditableLyricsArea**: Multi-line lyrics editor
- **AudioPlaybackThread**: Handles audio segment playback

### Performance Considerations
- Blocks are created on-demand when switching to Block View
- Audio playback uses separate thread to avoid UI blocking
- Large songs may have many blocks (scrollable interface)
- Memory usage scales with song length

## Troubleshooting

### Common Issues

#### Block View Not Updating
- Ensure transcription and chord detection are complete
- Check that audio file is loaded
- Verify that Gemini processing has finished

#### Audio Playback Not Working
- Check that audio file path is valid
- Ensure audio file format is supported
- Verify that audio player is properly initialized

#### Edits Not Saving
- Click "Save Changes" button after making edits
- Check that changes are reflected in Table View
- Verify that export functions use updated data

#### Performance Issues
- Large songs may take time to create blocks
- Audio playback may be slow on some systems
- Consider using Table View for very long songs

### Error Messages
- **"No audio file loaded"**: Load an audio file before using Block View
- **"No transcription data"**: Complete transcription before switching views
- **"Audio playback failed"**: Check audio file format and path

## Future Enhancements

### Planned Features
- **Customizable Block Size**: Allow users to change from 20 seconds
- **Batch Editing**: Edit multiple blocks simultaneously
- **Advanced Audio Controls**: Seek, loop, and volume controls
- **Visual Waveform**: Show audio waveform in blocks
- **Keyboard Shortcuts**: Quick navigation and editing shortcuts

### Integration Opportunities
- **Real-time Collaboration**: Share block edits between users
- **Version Control**: Track changes and revert edits
- **Export Formats**: Support for more export formats
- **Plugin System**: Allow third-party block editors

## Support

For issues with Block View:
1. Check that all required data is loaded
2. Verify audio file is accessible
3. Ensure transcription is complete
4. Test with the provided test script
5. Check the troubleshooting section above
