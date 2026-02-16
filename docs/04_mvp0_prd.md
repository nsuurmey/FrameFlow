# PRD: Speaking Clarity Tool — MVP 0 (Proof of Concept)

## Overview

A lightweight Python data science workflow for analyzing speaking practice recordings from an Android device. No AI models, no APIs, no transcription services — just raw audio analysis using Python libraries to validate the core methodology and measurement pipeline.

**Goal:** Prove the workflow works end-to-end (record → ingest → analyze → report) and establish that we can extract meaningful speaking metrics from .webm files before investing in Whisper transcription or Claude analysis.

---

## What This Is / What This Isn't

**This is:**
- A local Python script or Jupyter notebook
- Processing .webm files from Android Recorder
- Extracting audio-level metrics (no transcript needed)
- Producing a simple analysis report
- Something you can run in 5 minutes on a Chromebook or laptop

**This is not:**
- A CLI app with session management
- Transcription-based analysis
- AI-powered feedback or coaching
- A phased training regimen (that's MVP 1)

---

## Workflow

```
┌──────────────────────────────────────────┐
│  1. RECORD                               │
│     - Android Recorder app               │
│     - 2-3 minute speaking exercise       │
│     - Save .webm file                    │
├──────────────────────────────────────────┤
│  2. TRANSFER                             │
│     - Move .webm to working directory    │
│     - (Google Drive, USB, adb, etc.)     │
├──────────────────────────────────────────┤
│  3. INGEST                               │
│     - Python loads .webm via pydub/ffmpeg│
│     - Extract audio properties           │
│     - Convert to waveform for analysis   │
├──────────────────────────────────────────┤
│  4. ANALYZE (pure Python/signal proc)    │
│     - Silence/pause detection            │
│     - Speaking rate estimation            │
│     - Energy/volume profile              │
│     - Basic vocal variety metrics        │
├──────────────────────────────────────────┤
│  5. REPORT                               │
│     - Print metrics to console           │
│     - Generate simple visualizations     │
│     - Append to local CSV/JSON log       │
└──────────────────────────────────────────┘
```

---

## What We Can Measure Without Transcription

The key insight: a surprising amount of speaking quality signal lives in the audio waveform itself, before any transcription. These are the metrics we can extract with pure signal processing:

### M1: Total Duration & Speaking Time

- **Total duration:** Length of the recording
- **Speaking time:** Duration minus silence segments
- **Speaking ratio:** Speaking time / total duration (how much of the recording is actual speech vs. silence)
- **Library:** pydub, librosa

### M2: Silence / Pause Detection

This is the highest-value metric available without transcription. Pauses are directly observable in the audio signal.

- **Pause count:** Number of silence segments exceeding a threshold (e.g., >300ms)
- **Pause durations:** Distribution of pause lengths (short <0.5s, medium 0.5–2s, long >2s)
- **Pause placement:** Timestamps of each pause (early, middle, late in recording)
- **Pause rate:** Pauses per minute of speaking time
- **Long pause count:** Pauses >2s (potential filler-replacement or lost-thought moments)
- **Library:** pydub silence detection (`detect_silence`, `detect_nonsilent`), or librosa energy thresholding

**Why this matters:** The research says >80% of pauses should be at syntactic boundaries. We can't determine boundary placement without a transcript, but we CAN measure pause frequency, duration distribution, and whether pauses are evenly distributed or clustered — all useful baseline data.

**Tunable parameters:**
- Silence threshold (dBFS) — needs calibration per recording environment
- Minimum silence duration (ms) — 300ms is a reasonable starting point

### M3: Speaking Rate Proxy (Syllable Estimation)

Without transcription we can't count words, but we can estimate speaking rate from the audio signal:

- **Syllable rate estimation:** Detect amplitude peaks in the energy envelope as a proxy for syllable nuclei. Each vowel sound produces an energy peak. Count peaks per second → estimate syllables per minute.
- **Estimated WPM:** Syllables per minute ÷ 1.5 (average English syllables per word) gives a rough WPM estimate.
- **Rate variation:** Standard deviation of local speaking rate across 10-second windows. Low variation = monotone pacing. High variation = dynamic delivery (or erratic).
- **Library:** librosa (onset detection, energy envelope), scipy (peak detection)

**Benchmarks (from research):** 130–160 WPM optimal for presentations. Below 120 = lethargic. Above 180 = comprehension degrades.

### M4: Energy / Volume Profile

- **Mean energy:** Average loudness across the recording
- **Energy variance:** How much volume varies (low = monotone, high = dynamic)
- **Energy contour:** Plot energy over time — does volume drop off toward the end? (trailing off = common failure mode)
- **Peak moments:** Timestamps of highest energy (potential emphasis points)
- **Library:** librosa (RMS energy)

### M5: Pitch / Fundamental Frequency (F0)

- **Mean pitch:** Average fundamental frequency
- **Pitch range:** Min to max F0 (narrow = monotone, wide = expressive)
- **Pitch variance:** How much pitch varies over time
- **Uptalk detection:** Does pitch rise at the ends of phrases? (rising terminal = sounds like questions)
- **Library:** librosa (pyin pitch tracking), parselmouth (Praat wrapper for Python)

**Why this matters:** The research identifies monotone delivery as a diagnostic sign of cognitive overload. Pitch variance is a direct, audio-measurable proxy for vocal variety.

### M6: Session-Over-Session Tracking

- Append each session's metrics to a local CSV or JSON file
- Track trends across sessions
- Simple line charts: pause rate over time, estimated WPM over time, pitch variance over time

---

## Tech Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Audio loading | pydub + ffmpeg | Load .webm, convert to wav, extract properties |
| Signal analysis | librosa | Energy, pitch, onset detection, tempo |
| Pitch tracking | parselmouth (optional) | More accurate F0 via Praat algorithms |
| Silence detection | pydub or librosa | Pause identification and measurement |
| Peak detection | scipy.signal | Syllable estimation from energy envelope |
| Data storage | pandas + CSV or JSON | Session log, metrics history |
| Visualization | matplotlib | Waveform, energy contour, pitch contour, trend charts |
| Runtime | Python 3.10+ | Local execution, Jupyter or script |

**Dependencies:** `pip install pydub librosa matplotlib pandas scipy numpy`
Plus `ffmpeg` installed system-level for .webm handling.

Optional: `pip install parselmouth` for Praat-based pitch analysis.

---

## Output: Session Report

Each run produces a console report + optional plots:

```
═══════════════════════════════════════════
  SPEAKING CLARITY — SESSION REPORT
  Date: 2026-02-16  |  File: practice_001.webm
═══════════════════════════════════════════

DURATION
  Total:              2:47
  Speaking time:       2:12  (79% speaking ratio)

PAUSES
  Total pauses:       14
  Pauses/min:         6.4
  Short (<0.5s):      8
  Medium (0.5-2s):    4
  Long (>2s):         2
  Mean pause:         0.7s
  Longest pause:      3.1s at 1:42

SPEAKING RATE (estimated)
  Avg syllables/min:  228  (~152 WPM)
  Rate variation:     18.3 syl/min SD
  Rating:             ✓ Within optimal range (130-160 WPM)

ENERGY / VOLUME
  Mean RMS energy:    0.042
  Energy variance:    0.018
  Trailing off:       ⚠ Energy drops 34% in final 30s

PITCH (F0)
  Mean pitch:         142 Hz
  Pitch range:        98 - 214 Hz  (116 Hz range)
  Pitch variance:     24.7 Hz SD
  Uptalk instances:   3 detected

═══════════════════════════════════════════
  vs. LAST SESSION (practice_000.webm)
  Pauses/min:    8.1 → 6.4  ↓ (improving)
  Est. WPM:      168 → 152  ↓ (slowing toward target)
  Pitch range:   89 Hz → 116 Hz  ↑ (more variety)
═══════════════════════════════════════════
```

### Visualizations (matplotlib)

1. **Waveform + pause overlay:** Audio waveform with detected pauses highlighted in red
2. **Energy contour:** RMS energy over time — shows volume dynamics and trailing off
3. **Pitch contour:** F0 over time — shows monotone stretches and uptalk
4. **Speaking rate heatmap:** Estimated syllable rate in 10-second windows — shows where you speed up / slow down
5. **Session trends:** Line charts of key metrics across all sessions

---

## Data Storage

Simple CSV log (`clarity_log.csv`):

```csv
date,filename,duration_s,speaking_time_s,speaking_ratio,pause_count,pauses_per_min,mean_pause_s,long_pause_count,est_wpm,rate_variation,mean_energy,energy_variance,trailing_off_pct,mean_pitch_hz,pitch_range_hz,pitch_variance,uptalk_count
2026-02-16,practice_001.webm,167,132,0.79,14,6.4,0.7,2,152,18.3,0.042,0.018,0.34,142,116,24.7,3
```

Flat file, human-readable, easy to chart in any tool.

---

## Calibration Checklist

Before trusting the metrics, validate these with a few test recordings:

- [ ] **Silence threshold:** Record in your typical environment. Run silence detection. Are pauses correctly identified, or is background noise triggering false positives? Adjust dBFS threshold.
- [ ] **Syllable estimation accuracy:** Record yourself reading a passage with a known word count. Compare estimated WPM to actual WPM. Calibrate peak detection sensitivity.
- [ ] **.webm codec compatibility:** Run `ffprobe` on an Android Recorder .webm. Confirm pydub/ffmpeg can load it cleanly. Note the codec (likely Opus).
- [ ] **Pitch tracking quality:** Record a few sentences with deliberate pitch variation. Confirm F0 tracking follows your actual pitch, not noise artifacts.
- [ ] **Energy trailing off:** Record yourself deliberately trailing off at the end vs. finishing strong. Confirm the energy metric captures the difference.

---

## What This Validates for MVP 1

This proof of concept answers key questions before we invest in AI tooling:

| Question | How MVP 0 answers it |
|----------|---------------------|
| Can we reliably load Android .webm files? | Direct test with pydub/ffmpeg |
| Is the audio quality sufficient for analysis? | Validate signal-to-noise on real recordings |
| Can we detect pauses accurately? | Calibrate silence detection thresholds |
| Can we estimate speaking rate from audio? | Compare syllable estimation to known word counts |
| Does pitch/energy analysis yield useful signal? | Visualize and validate against perceived delivery |
| Is the workflow frictionless enough for daily use? | Time the full record → transfer → analyze cycle |
| What does the .webm codec look like? | `ffprobe` inspection, ffmpeg conversion test |
| Do metrics actually change session over session? | Run 3-5 sessions and check trend data |

---

## Stretch Goals (if basics work smoothly)

- **Auto-ingest from Google Drive folder:** Watch a folder for new .webm files, auto-analyze on drop
- **Filler sound detection (experimental):** Train a simple classifier on "um"/"uh" spectral signatures vs. speech. Even a rough heuristic (short low-energy voiced segments surrounded by pauses) might catch some fillers without transcription.
- **Comparative analysis:** Analyze a TED talk or podcast audio as a "gold standard" comparison for your own metrics
- **Jupyter dashboard:** Interactive notebook with widgets for loading files and viewing analysis
