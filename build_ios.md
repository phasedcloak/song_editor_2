# iOS Build Guide for Song Editor 2

## Overview
Building for iOS requires a different approach since the current PySide6-based application needs to be adapted for mobile platforms. Here are the recommended approaches:

## Option 1: Kivy + KivyMD (Recommended)

### Prerequisites
- macOS with Xcode installed
- Python 3.8+
- Kivy and KivyMD
- iOS deployment tools

### Setup Instructions

1. **Install Kivy and KivyMD:**
```bash
pip install kivy kivymd
```

2. **Install iOS deployment tools:**
```bash
pip install kivy-ios
```

3. **Create iOS project structure:**
```bash
toolchain build kivy
toolchain build numpy
toolchain build scipy
toolchain build soundfile
toolchain build requests
toolchain build aiohttp
toolchain build matplotlib
toolchain build torch
toolchain build demucs
toolchain build ctranslate2
toolchain build numba
toolchain build llvmlite
toolchain build tenacity
toolchain build pyyaml
```

4. **Create iOS-specific main.py:**
```python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.utils import platform

# Import your existing processing modules
from song_editor.processing.transcriber import Transcriber
from song_editor.processing.chords import ChordDetector
from song_editor.export.midi_export import export_midi

class SongEditorApp(App):
    def build(self):
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Song Editor 2', size_hint_y=None, height=50)
        layout.add_widget(title)
        
        # File selection
        file_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        self.file_chooser = FileChooserListView(path='.')
        file_layout.add_widget(self.file_chooser)
        
        select_btn = Button(text='Select File', size_hint_x=None, width=100)
        select_btn.bind(on_press=self.select_file)
        file_layout.add_widget(select_btn)
        
        layout.add_widget(file_layout)
        
        # Processing buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        
        transcribe_btn = Button(text='Transcribe')
        transcribe_btn.bind(on_press=self.transcribe_audio)
        btn_layout.add_widget(transcribe_btn)
        
        detect_chords_btn = Button(text='Detect Chords')
        detect_chords_btn.bind(on_press=self.detect_chords)
        btn_layout.add_widget(detect_chords_btn)
        
        export_btn = Button(text='Export MIDI')
        export_btn.bind(on_press=self.export_midi)
        btn_layout.add_widget(export_btn)
        
        layout.add_widget(btn_layout)
        
        # Results display
        self.results_text = TextInput(multiline=True, readonly=True)
        layout.add_widget(self.results_text)
        
        return layout
    
    def select_file(self, instance):
        if self.file_chooser.selection:
            self.selected_file = self.file_chooser.selection[0]
            self.results_text.text = f"Selected: {self.selected_file}"
    
    def transcribe_audio(self, instance):
        if hasattr(self, 'selected_file'):
            try:
                transcriber = Transcriber()
                words = transcriber.transcribe(self.selected_file)
                result = "Transcription:\n"
                for word in words:
                    result += f"{word.text} ({word.start:.2f}-{word.end:.2f})\n"
                self.results_text.text = result
            except Exception as e:
                self.results_text.text = f"Error: {str(e)}"
    
    def detect_chords(self, instance):
        if hasattr(self, 'selected_file'):
            try:
                detector = ChordDetector()
                chords = detector.detect_chords(self.selected_file)
                result = "Detected Chords:\n"
                for chord in chords:
                    result += f"{chord.symbol} ({chord.start:.2f}-{chord.end:.2f})\n"
                self.results_text.text = result
            except Exception as e:
                self.results_text.text = f"Error: {str(e)}"
    
    def export_midi(self, instance):
        if hasattr(self, 'selected_file'):
            try:
                output_file = self.selected_file.replace('.wav', '.mid')
                export_midi(self.selected_file, output_file)
                self.results_text.text = f"MIDI exported to: {output_file}"
            except Exception as e:
                self.results_text.text = f"Error: {str(e)}"

if __name__ == '__main__':
    SongEditorApp().run()
```

5. **Create buildozer.spec for iOS:**
```ini
[app]
title = Song Editor 2
package.name = songeditor2
package.domain = com.songeditor.app
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 2.0.0

requirements = python3,kivy,kivymd,numpy,scipy,soundfile,requests,aiohttp,matplotlib,torch,demucs,ctranslate2,numba,llvmlite,tenacity,pyyaml

orientation = portrait
fullscreen = 0
android.permissions = RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0

[buildozer]
log_level = 2
warn_on_root = 1
```

6. **Build for iOS:**
```bash
toolchain create SongEditor2 /path/to/your/project
cd SongEditor2-ios
toolchain run python main.py
```

## Option 2: BeeWare (Alternative)

### Setup Instructions

1. **Install BeeWare:**
```bash
python -m pip install briefcase
```

2. **Create BeeWare project:**
```bash
briefcase new
```

3. **Configure for iOS:**
```bash
briefcase create ios
briefcase build ios
briefcase run ios
```

## Option 3: React Native + Python Backend

### Architecture
- React Native frontend for UI
- Python backend running on server
- REST API communication

### Implementation Steps

1. **Create React Native app:**
```bash
npx react-native init SongEditor2Mobile
```

2. **Implement audio processing API:**
```python
# api_server.py
from flask import Flask, request, jsonify
from song_editor.processing.transcriber import Transcriber
from song_editor.processing.chords import ChordDetector

app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    transcriber = Transcriber()
    words = transcriber.transcribe(audio_file)
    return jsonify([{'text': w.text, 'start': w.start, 'end': w.end} for w in words])

@app.route('/detect-chords', methods=['POST'])
def detect_chords():
    audio_file = request.files['audio']
    detector = ChordDetector()
    chords = detector.detect_chords(audio_file)
    return jsonify([{'symbol': c.symbol, 'start': c.start, 'end': c.end} for c in chords])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

3. **React Native components:**
```javascript
// AudioProcessor.js
import React, { useState } from 'react';
import { View, Button, Text, Alert } from 'react-native';
import DocumentPicker from 'react-native-document-picker';

const AudioProcessor = () => {
  const [results, setResults] = useState(null);

  const pickAudio = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.audio],
      });
      
      const formData = new FormData();
      formData.append('audio', {
        uri: result[0].uri,
        type: 'audio/wav',
        name: result[0].name,
      });

      const response = await fetch('http://your-server:5000/transcribe', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      Alert.alert('Error', 'Failed to process audio');
    }
  };

  return (
    <View>
      <Button title="Select Audio File" onPress={pickAudio} />
      {results && (
        <Text>{JSON.stringify(results, null, 2)}</Text>
      )}
    </View>
  );
};

export default AudioProcessor;
```

## iOS-Specific Considerations

### Permissions
Add to Info.plist:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for audio recording</string>
<key>NSDocumentsFolderUsageDescription</key>
<string>This app needs access to documents for audio files</string>
```

### Audio Session Configuration
```python
from kivy.core.audio import SoundLoader
import avfoundation

# Configure audio session for iOS
avfoundation.AVAudioSession.sharedInstance().setCategory_(
    avfoundation.AVAudioSessionCategoryPlayAndRecord,
    error=None
)
```

### Performance Optimization
- Use background processing for heavy audio operations
- Implement proper memory management for large audio files
- Cache processed results to avoid recomputation

### Testing
- Test on physical iOS devices (not just simulator)
- Test with various audio file formats
- Test memory usage with large files
- Test background/foreground transitions

## Deployment

### App Store Requirements
1. **Code Signing:** Use Apple Developer account
2. **App Store Connect:** Configure app metadata
3. **Screenshots:** Create for different device sizes
4. **Privacy Policy:** Required for audio processing apps
5. **App Review:** Ensure compliance with App Store guidelines

### Distribution
- TestFlight for beta testing
- App Store for public release
- Enterprise distribution for internal use

## Troubleshooting

### Common Issues
1. **Audio permissions:** Ensure proper permission requests
2. **Memory limits:** iOS has stricter memory constraints
3. **Background processing:** Use background tasks for long operations
4. **File access:** Use proper iOS file system APIs

### Debug Tools
- Xcode Instruments for performance profiling
- Console.app for system logs
- TestFlight for crash reporting
