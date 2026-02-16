# Clarity: Speaking Clarity Practice Tool

A CLI-based tool for analyzing audio recordings and providing feedback on speaking clarity metrics. Helps you practice and improve extemporaneous speaking skills.

## Features

**MVP 0 (Current Release)** provides core analysis capabilities:

- **Audio Ingestion**: Load `.webm` audio files (e.g., from Android Recorder)
- **Speech Metrics**:
  - Speaking rate (words per minute)
  - Filler word detection (um, uh, like, etc.)
  - Pause detection and analysis
  - Energy/volume metrics
  - Pitch analysis
- **Progress Tracking**: CSV logging of all practice sessions
- **Visualization**: Time-series plots and markdown reports

## Installation

### Prerequisites

- **Python 3.10+**
- **ffmpeg** (required for audio processing)

#### Install ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install Clarity

```bash
# Clone the repository
git clone https://github.com/nsuurmey/FrameFlow.git
cd FrameFlow

# Install in editable mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Quick Start

### 1. Analyze an Audio Recording

```bash
python -m clarity analyze recording.webm
```

**Output:**
```
Analyzing: recording.webm

✓ Audio loaded (4.68s, 16000 Hz)

Running analysis...
  [1/6] Transcribing audio...
  [2/6] Detecting filler words...
  [3/6] Detecting pauses...
  [4/6] Calculating speaking rate...
  [5/6] Analyzing energy...
  [6/6] Analyzing pitch...

============================================================
TRANSCRIPT
============================================================
[Your transcribed speech...]

============================================================
SPEAKING RATE
============================================================
  Words: 42
  WPM: 150.5
  Duration: 16.75s

[... more metrics ...]

✓ Results logged to: clarity_log.csv
```

### 2. Generate Progress Report

After analyzing multiple recordings:

```bash
python -m clarity report
```

**Output:**
```
Generating report from 5 sessions...
✓ Plot saved to: metrics_plot.png
✓ Report saved to: clarity_report.md

✓ Report generation complete!
```

### 3. View Your Progress

Open `clarity_report.md` to see:
- Summary statistics (mean, std dev, min, max) for all metrics
- Table of recent sessions
- Progress notes comparing your first and latest sessions
- Time-series plots showing trends

## Usage Examples

### Record and Analyze

1. **Record yourself** speaking (using Android Recorder, QuickTime, etc.)
2. **Export as .webm** (or other ffmpeg-supported format)
3. **Analyze**: `python -m clarity analyze my_recording.webm`
4. **Review** the metrics and identify areas to improve
5. **Practice** and record again
6. **Track progress**: `python -m clarity report`

### Typical Workflow

```bash
# Session 1
python -m clarity analyze practice1.webm

# Session 2
python -m clarity analyze practice2.webm

# Session 3
python -m clarity analyze practice3.webm

# View progress
python -m clarity report
```

## Metrics Explained

### Speaking Rate (WPM)
- **Target**: 120-180 WPM (conversational), 150-200 WPM (presentations)
- **Too slow**: <100 WPM may sound hesitant
- **Too fast**: >200 WPM may be hard to follow

### Filler Words
- Common fillers: um, uh, like, you know, actually, basically
- **Goal**: Minimize fillers, especially in formal speaking
- **Typical**: 1-5 fillers per minute is common in casual speech

### Pauses
- **Pause count**: Number of silent segments detected
- **Pause percentage**: % of total audio that is silence
- **Strategic pauses** can improve clarity and emphasis
- **Excessive pauses** (>40%) may indicate hesitation

### Energy (dB)
- Measures average volume/loudness
- **Consistency matters**: Low std dev = more consistent delivery
- **Range**: Shows dynamic range of your voice

### Pitch (Hz)
- Fundamental frequency of your voice
- **Typical ranges**:
  - Male: 85-180 Hz
  - Female: 165-255 Hz
- **Variation** (pitch range) adds expressiveness

## Known Limitations (MVP 0)

### Transcription Accuracy
- **MVP 0** uses a fallback transcriber due to network constraints
- Transcription is estimated based on speaking duration (150 WPM baseline)
- **Impact**:
  - WPM calculations are approximate
  - Filler word detection may miss actual fillers in speech
- **Workaround**: Manually count words and fillers for calibration
- **Future**: Full Whisper integration planned for MVP 1

### Audio Format Support
- Primary support: `.webm` files (Android Recorder default)
- Other formats work if ffmpeg supports them
- Always test with a short clip first

### Pause Detection Sensitivity
- Uses energy-based thresholding
- May not detect very short pauses (<300ms)
- Background noise can affect detection

### Pitch Detection
- Works best with clear, voiced speech
- May return 0 Hz if no voiced segments detected
- Accuracy depends on audio quality

## Testing

Run the test suite:

```bash
# All tests
make check

# Just tests
make test

# Specific test file
python -m pytest tests/test_calibration.py -v
```

## Development

### Project Structure

```
FrameFlow/
├── src/clarity/
│   ├── __main__.py           # CLI entry point
│   ├── audio_loader.py       # Audio file loading
│   ├── analyzers/            # Analysis modules
│   │   ├── analyzer.py       # Main analyzer
│   │   ├── filler_detector.py
│   │   ├── pause_detector.py
│   │   ├── speaking_rate.py
│   │   ├── energy_analyzer.py
│   │   ├── pitch_analyzer.py
│   │   └── transcriber.py
│   └── reporting/            # Reporting & visualization
│       ├── csv_logger.py
│       ├── plotter.py
│       └── report_generator.py
├── tests/                    # Test suite
├── docs/                     # Phase 0 planning documents
└── pyproject.toml           # Project configuration
```

### Code Quality

```bash
make lint      # Run ruff linter
make test      # Run pytest
make typecheck # Run mypy
make check     # Run all checks
```

## Roadmap

### MVP 0 (Current) ✓
- [x] Audio ingestion pipeline
- [x] Core metric analyzers
- [x] CSV logging
- [x] Progress reports and plots
- [x] Validation and calibration

### MVP 1 (Planned)
- [ ] Full Whisper transcription integration
- [ ] Improved WPM accuracy
- [ ] Real-time filler detection during recording
- [ ] Web interface
- [ ] Mobile app integration

## Troubleshooting

### "FFmpeg not found"
Install ffmpeg using your system package manager (see Installation section).

### "Whisper model unavailable"
This is expected in MVP 0. The fallback transcriber will be used automatically.

### Low WPM values
If using the fallback transcriber, WPM is estimated. For accurate WPM:
1. Manually count words in your recording
2. Use duration from Clarity
3. Calculate: (word_count / duration_seconds) * 60

### No pitch detected
Ensure:
- Audio contains voiced speech (not just whispers/silence)
- Audio quality is good (no excessive noise)
- Recording level is adequate (not too quiet)

## Contributing

This is a personal practice tool developed as part of learning software engineering. Feedback and suggestions welcome!

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built using:
- [librosa](https://librosa.org/) - Audio analysis
- [pydub](http://pydub.com/) - Audio manipulation
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Speech recognition
- [matplotlib](https://matplotlib.org/) - Visualization

---

**Note**: This is MVP 0 - a foundational release focused on core functionality. Accuracy will improve in future versions with full Whisper integration and calibrated thresholds.
