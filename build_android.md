# Android Build Guide for Song Editor 2

## Overview
Building for Android requires adapting the PySide6-based application for mobile platforms. Here are the recommended approaches:

## Option 1: Kivy + KivyMD (Recommended)

### Prerequisites
- Linux, macOS, or Windows
- Python 3.8+
- Android SDK and NDK
- Java JDK 8 or 11
- Kivy and KivyMD

### Setup Instructions

1. **Install Kivy and KivyMD:**
```bash
pip install kivy kivymd
```

2. **Install Buildozer:**
```bash
pip install buildozer
```

3. **Initialize Buildozer:**
```bash
buildozer init
```

4. **Configure buildozer.spec:**
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
android.permissions = RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.api = 29
android.minapi = 21
android.ndk = 23b
android.sdk = 29
android.accept_sdk_license = True
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
```

5. **Create Android-specific main.py:**
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
from kivy.clock import Clock
from kivy.lang import Builder

# Import your existing processing modules
from song_editor.processing.transcriber import Transcriber
from song_editor.processing.chords import ChordDetector
from song_editor.export.midi_export import export_midi

# KV language string for UI
KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: '10dp'
    spacing: '10dp'
    
    Label:
        text: 'Song Editor 2'
        size_hint_y: None
        height: '50dp'
        font_size: '20sp'
    
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '50dp'
        
        FileChooserListView:
            id: file_chooser
            path: '.'
        
        Button:
            text: 'Select File'
            size_hint_x: None
            width: '100dp'
            on_press: app.select_file()
    
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: '50dp'
        
        Button:
            text: 'Transcribe'
            on_press: app.transcribe_audio()
        
        Button:
            text: 'Detect Chords'
            on_press: app.detect_chords()
        
        Button:
            text: 'Export MIDI'
            on_press: app.export_midi()
    
    TextInput:
        id: results_text
        multiline: True
        readonly: True
        hint_text: 'Results will appear here...'
'''

class SongEditorApp(App):
    def build(self):
        return Builder.load_string(KV)
    
    def select_file(self):
        if self.root.ids.file_chooser.selection:
            self.selected_file = self.root.ids.file_chooser.selection[0]
            self.root.ids.results_text.text = f"Selected: {self.selected_file}"
    
    def transcribe_audio(self):
        if hasattr(self, 'selected_file'):
            try:
                self.root.ids.results_text.text = "Transcribing... Please wait."
                Clock.schedule_once(lambda dt: self._transcribe_worker(), 0.1)
            except Exception as e:
                self.root.ids.results_text.text = f"Error: {str(e)}"
    
    def _transcribe_worker(self):
        try:
            transcriber = Transcriber()
            words = transcriber.transcribe(self.selected_file)
            result = "Transcription:\n"
            for word in words:
                result += f"{word.text} ({word.start:.2f}-{word.end:.2f})\n"
            self.root.ids.results_text.text = result
        except Exception as e:
            self.root.ids.results_text.text = f"Error: {str(e)}"
    
    def detect_chords(self):
        if hasattr(self, 'selected_file'):
            try:
                self.root.ids.results_text.text = "Detecting chords... Please wait."
                Clock.schedule_once(lambda dt: self._detect_chords_worker(), 0.1)
            except Exception as e:
                self.root.ids.results_text.text = f"Error: {str(e)}"
    
    def _detect_chords_worker(self):
        try:
            detector = ChordDetector()
            chords = detector.detect_chords(self.selected_file)
            result = "Detected Chords:\n"
            for chord in chords:
                result += f"{chord.symbol} ({chord.start:.2f}-{chord.end:.2f})\n"
            self.root.ids.results_text.text = result
        except Exception as e:
            self.root.ids.results_text.text = f"Error: {str(e)}"
    
    def export_midi(self):
        if hasattr(self, 'selected_file'):
            try:
                output_file = self.selected_file.replace('.wav', '.mid')
                export_midi(self.selected_file, output_file)
                self.root.ids.results_text.text = f"MIDI exported to: {output_file}"
            except Exception as e:
                self.root.ids.results_text.text = f"Error: {str(e)}"

if __name__ == '__main__':
    SongEditorApp().run()
```

6. **Build for Android:**
```bash
buildozer android debug
```

7. **Install on device:**
```bash
buildozer android debug deploy run
```

## Option 2: Chaquopy (Python in Android)

### Setup Instructions

1. **Create Android Studio project:**
```bash
# Create new Android project
# Add Chaquopy plugin to build.gradle
```

2. **Configure build.gradle:**
```gradle
plugins {
    id 'com.chaquo.python'
}

android {
    defaultConfig {
        ndk {
            abiFilters "armeabi-v7a", "arm64-v8a", "x86", "x86_64"
        }
    }
}

chaquopy {
    defaultConfig {
        version "3.8"
        pip {
            install "numpy"
            install "scipy"
            install "soundfile"
            install "requests"
            install "aiohttp"
            install "matplotlib"
            install "torch"
            install "demucs"
            install "ctranslate2"
            install "numba"
            install "llvmlite"
            install "tenacity"
            install "pyyaml"
        }
    }
}
```

3. **Create Python module:**
```python
# app/src/main/python/song_processor.py
from song_editor.processing.transcriber import Transcriber
from song_editor.processing.chords import ChordDetector
from song_editor.export.midi_export import export_midi

class SongProcessor:
    def __init__(self):
        self.transcriber = Transcriber()
        self.chord_detector = ChordDetector()
    
    def transcribe(self, audio_path):
        return self.transcriber.transcribe(audio_path)
    
    def detect_chords(self, audio_path):
        return self.chord_detector.detect_chords(audio_path)
    
    def export_midi(self, audio_path, output_path):
        return export_midi(audio_path, output_path)
```

4. **Java interface:**
```java
// MainActivity.java
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {
    private Python py;
    private PyObject songProcessor;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        py = Python.getInstance();
        songProcessor = py.getModule("song_processor").callAttr("SongProcessor");
    }
    
    public void transcribeAudio(String audioPath) {
        PyObject result = songProcessor.callAttr("transcribe", audioPath);
        // Handle result
    }
}
```

## Option 3: Flutter + Python Backend

### Architecture
- Flutter frontend for UI
- Python backend running on server
- REST API communication

### Implementation Steps

1. **Create Flutter app:**
```bash
flutter create song_editor_mobile
cd song_editor_mobile
```

2. **Add dependencies to pubspec.yaml:**
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^0.13.5
  file_picker: ^5.2.10
  path_provider: ^2.0.15
  permission_handler: ^10.2.0
```

3. **Create Flutter UI:**
```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:io';

void main() {
  runApp(SongEditorApp());
}

class SongEditorApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Song Editor 2',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: SongEditorHome(),
    );
  }
}

class SongEditorHome extends StatefulWidget {
  @override
  _SongEditorHomeState createState() => _SongEditorHomeState();
}

class _SongEditorHomeState extends State<SongEditorHome> {
  String? selectedFile;
  String results = '';
  bool isProcessing = false;

  Future<void> pickAudioFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
    );

    if (result != null) {
      setState(() {
        selectedFile = result.files.single.path;
      });
    }
  }

  Future<void> transcribeAudio() async {
    if (selectedFile == null) return;

    setState(() {
      isProcessing = true;
      results = 'Transcribing... Please wait.';
    });

    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('http://your-server:5000/transcribe'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('audio', selectedFile!),
      );

      var response = await request.send();
      var responseData = await response.stream.bytesToString();

      setState(() {
        results = responseData;
        isProcessing = false;
      });
    } catch (e) {
      setState(() {
        results = 'Error: $e';
        isProcessing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Song Editor 2'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            ElevatedButton(
              onPressed: pickAudioFile,
              child: Text('Select Audio File'),
            ),
            SizedBox(height: 16),
            if (selectedFile != null)
              Text('Selected: ${selectedFile!.split('/').last}'),
            SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: isProcessing ? null : transcribeAudio,
                    child: Text('Transcribe'),
                  ),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: isProcessing ? null : () {},
                    child: Text('Detect Chords'),
                  ),
                ),
              ],
            ),
            SizedBox(height: 16),
            Expanded(
              child: Container(
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: SingleChildScrollView(
                  child: Text(results),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Android-Specific Considerations

### Permissions
Add to AndroidManifest.xml:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.INTERNET" />
```

### Runtime Permissions
```python
from android.permissions import request_permissions, Permission

# Request permissions at runtime
request_permissions([
    Permission.RECORD_AUDIO,
    Permission.WRITE_EXTERNAL_STORAGE,
    Permission.READ_EXTERNAL_STORAGE
])
```

### Performance Optimization
- Use background threads for heavy processing
- Implement proper memory management
- Cache processed results
- Use Android's WorkManager for background tasks

### File Access
```python
from android.storage import primary_external_storage_path
import os

# Get Android storage path
storage_path = primary_external_storage_path()
audio_dir = os.path.join(storage_path, 'Music')
```

### Audio Recording
```python
from kivy.core.audio import SoundLoader
from android.mixer import AndroidMixer

# Configure audio for Android
mixer = AndroidMixer()
mixer.init()
```

## Testing

### Emulator Testing
- Test on different API levels (21-33)
- Test on different screen sizes
- Test with different Android versions

### Device Testing
- Test on physical Android devices
- Test with various audio file formats
- Test memory usage with large files
- Test background/foreground transitions

## Deployment

### Google Play Store Requirements
1. **Signing:** Use Android App Bundle (AAB)
2. **Google Play Console:** Configure app metadata
3. **Screenshots:** Create for different device sizes
4. **Privacy Policy:** Required for audio processing apps
5. **App Review:** Ensure compliance with Play Store guidelines

### Distribution
- Internal testing track
- Closed testing track
- Open testing track
- Production release

## Troubleshooting

### Common Issues
1. **Permission errors:** Ensure proper permission requests
2. **Memory issues:** Android has memory constraints
3. **Background processing:** Use proper background task APIs
4. **File access:** Use proper Android file system APIs

### Debug Tools
- Android Studio Profiler
- Logcat for debugging
- Firebase Crashlytics for crash reporting

### Build Issues
```bash
# Clean build
buildozer android clean

# Debug build with verbose output
buildozer android debug -v

# Check buildozer configuration
buildozer android debug deploy run logcat
```
