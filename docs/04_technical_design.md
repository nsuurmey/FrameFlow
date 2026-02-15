# Technical Design: Speaking Clarity Practice Tool

## 1. Project Overview

A standalone Python CLI tool that implements a structured 90-day speaking improvement program. Users record speech externally on Android Recorder, upload `.webm` audio files, and receive phase-aware analysis and feedback powered by Whisper (transcription) and Claude (analysis). All state lives in a single portable JSON file — no databases, no servers, no accounts.

**Scope:** MVP1 delivers the complete daily practice loop — session setup, `.webm` transcription via local Whisper, full analysis engine (fillers, mazes, hedging, framework checks, 5-dimension scoring), phase-gated feedback, baseline recording, session history, and local persistence. **Non-goals for MVP1:** additional audio formats, audio-level vocal analysis (pitch/volume), real-time recording, cloud sync, team/peer features, calendar integration, and any web or mobile UI.

---

## 2. System Architecture

### 2.1 Component Map

```
┌──────────────────────────────────────────────────────┐
│                    CLI Interface                      │
│              (click or typer framework)               │
│                                                      │
│  Commands:                                           │
│    practice   — full session workflow                 │
│    baseline   — first-run baseline recording          │
│    history    — view past sessions & trends           │
│    status     — current phase, streak, next targets   │
│    review <id>— re-display a past session analysis    │
│    weekly     — weekly summary report                 │
│    export     — dump metrics for external charting    │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│               Session Orchestrator                    │
│                                                      │
│  Coordinates the full workflow:                       │
│  setup → warm-up → input → transcribe → analyze →    │
│  score → feedback → persist                          │
└──┬──────────┬──────────┬──────────┬──────────┬───────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌───────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Session│ │Audio   │ │Analysis│ │Feedback│ │Storage │
│Setup  │ │Pipeline│ │Engine  │ │Engine  │ │Manager │
│       │ │        │ │        │ │        │ │        │
│Topic  │ │ffmpeg  │ │Claude  │ │Score-  │ │JSON    │
│gen,   │ │convert,│ │API     │ │card,   │ │read/   │
│frame- │ │Whisper │ │call w/ │ │tips,   │ │write,  │
│work,  │ │trans-  │ │rubric  │ │trend   │ │phase   │
│warm-up│ │cribe,  │ │prompt  │ │compare │ │transi- │
│params │ │extract │ │        │ │        │ │tion    │
│       │ │timing  │ │        │ │        │ │logic   │
└───────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 2.2 Component Details

- **CLI Interface**
  - Framework: `typer` (lightweight, type-hint-driven CLI framework)
  - Rich terminal output via `rich` (tables, progress bars, colored scorecards)
  - Handles user prompts (topic override, comfort rating, transcript paste)

- **Session Orchestrator**
  - State machine driving the 7-step workflow from the PRD
  - Manages phase context — reads current phase from storage, passes to all components
  - Handles both `.webm` upload path and transcript paste fallback path

- **Session Setup Module**
  - Topic generation: phase-aware topic pool with rotation tracking (avoids repeats)
  - Framework assignment: deterministic mapping from topic type → framework (PRD table)
  - Focus skill selection: picks 1-2 from phase-appropriate pool, weighted toward weak areas
  - Warm-up display: phase-specific exercises rendered as formatted instructions
  - Phase 3 daily rotation: day-of-week schedule (Mon-Fri) per PRD

- **Audio Pipeline**
  - `ffmpeg` subprocess: `.webm` → `.wav` conversion (Opus/Vorbis codec handling)
  - `openai-whisper` Python library: transcription with `--word_timestamps=True`
  - Duration extraction from Whisper output (start/end timestamps)
  - WPM calculation: `word_count / (duration_seconds / 60)`
  - Filler clustering: map filler word positions to speech segments (opening, middle, closing, transitions)
  - Temp file cleanup after transcription

- **Analysis Engine**
  - Single Claude API call per session (stateless)
  - Prompt assembly: rubric + phase config + framework def + filler/maze/hedge lexicons + last 5 session metrics + transcript
  - Structured JSON output via Claude (matching PRD session schema)
  - Phase-gating logic: only request scores for active dimensions
  - Filler disambiguation guidance embedded in prompt (few-shot examples)

- **Feedback Engine**
  - Scorecard renderer: phase-gated dimension scores + composite
  - Tip formatter: 3 tips with transcript excerpts, technique references
  - Trend comparator: current vs. last 5 sessions, current vs. baseline
  - Phase milestone tracker: sessions remaining, metric gaps to next phase
  - Overcorrection detector: flag if filler rate = 0 for 3+ consecutive sessions

- **Storage Manager**
  - Single `clarity_sessions.json` file (PRD schema)
  - Atomic writes (write to temp file, then rename — prevents corruption)
  - Phase transition logic: evaluate thresholds after each session, record transitions
  - Metrics history append (flat arrays for easy trend access)
  - Baseline recording and comparison

### 2.3 Data Store

- **Primary:** `~/.clarity/clarity_sessions.json` (single file, PRD schema)
- **Audio archive:** `~/.clarity/audio/session_NNN.webm` (optional, user can disable to save space)
- **Config:** `~/.clarity/config.json` (Whisper model size, audio archive toggle, API key reference)

### 2.4 External Dependencies

| Dependency | Purpose | Install |
|-----------|---------|---------|
| `openai-whisper` | Local transcription | `pip install openai-whisper` |
| `ffmpeg` | `.webm` → `.wav` conversion | System package |
| `anthropic` | Claude API for analysis | `pip install anthropic` |
| `typer` | CLI framework | `pip install typer` |
| `rich` | Terminal formatting | `pip install rich` |
| `torch` | Whisper's ML backend | Pulled by whisper |

### 2.5 Key Design Decisions

1. **Python chosen** — natural fit for Whisper (native Python library), eliminates shell-out complexity, and positions well for MVP2 audio analysis (librosa).
2. **Local Whisper, not cloud** — preserves privacy (speech recordings stay on-device), eliminates API cost for transcription, works offline after initial download.
3. **Vocal Delivery = self-rating in MVP1** — user provides 1-5 rating at end of session. Deferred to MVP2 for audio-derived scoring.
4. **Single Claude API call per session** — the analysis prompt is large (~2-3K tokens of rubric/context + transcript) but one call keeps latency predictable and cost low (~$0.02-0.05/session).
5. **`typer` + `rich` over `click`** — less boilerplate, better type safety, `rich` gives polished output with zero frontend investment.
6. **Atomic JSON writes** — write-to-temp-then-rename prevents data loss from crashes mid-write.

---

## 3. Milestone-Based Delivery Plan

### Team Allocation (3 engineers)

| Engineer | Primary Domain |
|----------|---------------|
| E1 | Audio pipeline + CLI framework + storage |
| E2 | Analysis engine (prompt engineering + Claude integration) |
| E3 | Session setup + feedback engine + phase logic |

### MVP1: Core Daily Loop (Weeks 1–9)

**Objective:** A user can run a complete daily practice session end-to-end — get a topic, record externally, upload `.webm`, receive scored analysis with tips, and track progress across sessions. Phase 1 fully functional; Phase 2/3 logic present and testable.

#### Sprint 1 (Weeks 1-2): Foundation & Audio Pipeline

| Work Item | Owner | Description |
|-----------|-------|-------------|
| Project scaffolding | E1 | Python package structure, `pyproject.toml`, dev tooling (ruff, pytest, mypy), CI skeleton |
| CLI skeleton | E1 | `typer` app with `practice`, `baseline`, `history`, `status` commands (stub implementations) |
| Storage manager | E1 | JSON read/write with atomic saves, schema validation, init on first run |
| Audio pipeline | E1 | `.webm` → ffmpeg → `.wav` → Whisper → transcript + timestamps. Codec detection via ffprobe. |
| Whisper fidelity testing | E1 | Record test `.webm` files with deliberate fillers. Test `tiny`, `base`, `small`, `medium` models. Document which model reliably preserves fillers. **This is a blocker — determines model choice.** |
| Analysis prompt v1 | E2 | Draft the core analysis prompt: rubric, filler lexicon, framework definitions, few-shot disambiguation examples. Test against hand-crafted transcripts. |
| Phase configuration | E3 | Data models for phases 1/2/3: metrics tracked, frameworks available, topic types, prep times, durations, warm-ups, transition thresholds. |
| Topic pool | E3 | Phase-aware topic bank (15-20 topics per phase), rotation tracking. |

**Key deliverable:** Can upload a `.webm`, get a raw transcript with timestamps, and see it printed in the terminal. Analysis prompt drafted and tested against 3-5 sample transcripts.

#### Sprint 2 (Weeks 3-4): Analysis Engine & Session Setup

| Work Item | Owner | Description |
|-----------|-------|-------------|
| Duration/WPM extraction | E1 | Calculate from Whisper timestamps. Filler position mapping (opening/middle/closing/transition segments). |
| Transcript paste fallback | E1 | Manual duration input for paste path. Shared interface with audio path. |
| Claude API integration | E2 | `anthropic` SDK call with structured JSON output parsing. Error handling, retries, timeout config. |
| Analysis prompt v2 | E2 | Iterate prompt based on Sprint 1 testing. Add maze detection rubric, hedging lexicon. Calibrate scoring against 10+ transcripts with known "correct" scores. |
| Phase-gating in prompt | E2 | Dynamic prompt assembly — only include rubric sections for active phase metrics. |
| Session setup flow | E3 | Full setup: phase detection → warm-up display → topic generation → framework assignment → focus skill selection → session brief display. |
| Framework completion check | E3 | Define checking logic for each framework (PREP, What-So What-Now What, Problem-Solution-Benefit, STAR, Pyramid). |
| Baseline flow | E3 | First-run detection, baseline session workflow, baseline storage. |

**Key deliverable:** Full `practice` command works end-to-end for Phase 1 — setup, upload, transcription, analysis, and raw JSON output of results.

#### Sprint 3 (Weeks 5-6): Feedback, Scoring & History

| Work Item | Owner | Description |
|-----------|-------|-------------|
| Scorecard renderer | E3 | `rich` table: dimension scores, composite score, benchmark ratings. Phase-gated display. |
| Tip formatter | E3 | Parse Claude's tips, format with transcript excerpts and technique references. |
| Trend comparator | E3 | Last-5-session comparison, baseline delta, streak tracking. |
| Phase transition engine | E3 | Evaluate thresholds after each session. Trigger transition with user notification. |
| History commands | E1 | `history` (last N sessions table), `review <id>` (full session detail), `status` (phase + streak + targets). |
| Weekly summary | E1 | Aggregate metrics for the current week, display as formatted report. |
| Prompt calibration | E2 | Run analysis against 20+ varied transcripts. Tune scoring consistency. Document calibration results. |
| Overcorrection detection | E2 | Detect 0-filler streak, generate appropriate feedback. |
| Comfort rating input | E3 | Post-session self-rating prompt (1-10) for subjective comfort. |

**Key deliverable:** Complete `practice` loop with polished terminal output — scorecard, tips, trends. `history` and `status` commands functional.

#### Sprint 4 (Weeks 7-8): Phase 2/3, Polish & Edge Cases

| Work Item | Owner | Description |
|-----------|-------|-------------|
| Phase 2 exercises | E3 | Persuasive topics, Feynman drill, repeat-and-improve flow (2 recordings per session). |
| Phase 3 exercises | E3 | Daily rotation, hostile Q&A topic generation, argue-both-sides flow, random-word story. |
| Full phase testing | E3 | Simulate progression through all phases with test data. Verify transition logic. |
| Error handling hardening | E1 | ffmpeg missing, Whisper download failure, corrupted .webm, API timeout, malformed JSON. |
| Config management | E1 | `~/.clarity/config.json` — Whisper model selection, audio archive toggle, API key. |
| Export command | E1 | CSV/JSON export of metrics history for external charting. |
| Prompt final tuning | E2 | Final calibration pass. Filler disambiguation edge cases. Scoring consistency audit. |
| End-to-end testing | All | Full 5-session simulated arc through Phase 1. Bug bash. |

**Key deliverable:** All three phases functional. Error paths handled gracefully. Ready for real daily use.

#### Sprint 5 (Week 9): Buffer & Launch Prep

| Work Item | Owner | Description |
|-----------|-------|-------------|
| Bug fixes from testing | All | Address issues found in Sprint 4 E2E testing. |
| README & install guide | E1 | Setup instructions: Python version, ffmpeg install, Whisper model download, API key config. |
| Dogfooding | All | Each engineer uses the tool for 3+ real sessions. Capture friction points. |
| Performance baseline | E1 | Measure: Whisper transcription time by model size, Claude API latency, total session wall time. Ensure <10 min total workflow. |

**Key deliverable:** MVP1 shipped. Tool usable for daily practice.

---

### MVP2: Format Expansion & Audio Analysis (Weeks 10-16, estimated)

**Objective:** Support additional audio formats, transcript file import, and audio-derived vocal delivery scoring.

- **Key user-facing changes:**
  - Accept `.mp3`, `.wav`, `.m4a` uploads
  - Import transcript files (`.txt`, `.md`) from Whisper Flow / Granola
  - Vocal delivery scored from audio features (pitch variance, volume dynamics) instead of self-rating
  - Audio-level pause detection: duration and placement → true pause quality scoring
  - Exportable markdown progress reports with inline trend charts (sparklines)

- **Technical work:**
  - `librosa` integration for pitch/volume extraction
  - Pause detection from Whisper timestamp gaps (validate threshold: >0.5s)
  - Format detection and conversion pipeline generalization
  - Transcript file parser with format normalization
  - Updated analysis prompt with audio-derived features
  - Markdown report generator with trend visualization

### GA: Full Feature Set (Weeks 17-24, estimated)

**Objective:** Real-time recording, live Claude interaction, and collaborative features.

- **Key user-facing changes:**
  - Record directly within the CLI (no external app needed)
  - Live hostile Q&A with Claude generating questions in real-time
  - Side-by-side session comparison
  - Custom topic/skill libraries
  - 30/60/90-day milestone reports with full baseline comparison
  - Calendar integration for daily reminders

- **Technical work:**
  - `pyaudio` or `sounddevice` for in-CLI recording
  - Streaming Claude interaction for live Q&A
  - Comparison view rendering
  - User-defined topic/framework storage
  - System notification / cron integration for reminders

---

## 4. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **Whisper drops fillers on transcription.** Larger models may "correct" disfluencies, destroying the core signal. | High | Critical | Sprint 1 blocker: test all model sizes against .webm recordings with deliberate fillers. If no model preserves fillers reliably, evaluate `whisper-timestamped` fork or `faster-whisper` with VAD disabled. Document minimum viable model. |
| 2 | **Android Recorder .webm codec incompatibility.** Opus/Vorbis codec variant may not convert cleanly via ffmpeg or may cause Whisper errors. | Medium | High | Sprint 1: test with actual Android Recorder output. ffprobe codec check as first step in pipeline. Fail fast with clear error message and codec info if unsupported. |
| 3 | **Claude scoring inconsistency.** Same transcript produces different scores across runs, undermining user trust in progress tracking. | High | High | Calibration phase in Sprint 2-3: run same transcripts multiple times, measure variance. Use `temperature=0` on API calls. Add few-shot scoring examples in prompt. Consider caching analysis results so re-analysis is opt-in. |
| 4 | **Analysis prompt exceeds context window / cost spirals.** Full rubric + lexicons + history + transcript may be large. | Medium | Medium | Measure prompt size early. Budget: ~2K rubric + ~1K history + ~1-3K transcript = ~4-6K tokens. Well within limits. Phase-gate rubric sections to keep prompt lean in early phases. Monitor cost per session. |
| 5 | **Whisper transcription is too slow for 10-min workflow target.** A 2-3 min recording on CPU with `medium` model could take 3-5 min to transcribe. | High | High | Test wall-clock time in Sprint 1. If too slow: (a) use `small` model if filler fidelity allows, (b) recommend `faster-whisper` (CTranslate2 backend, 4x speedup), (c) document GPU setup for power users. Set a 2-minute transcription budget. |
| 6 | **Filler word disambiguation is unreliable.** "Like," "so," "well" misclassified as fillers when used meaningfully, or vice versa. | High | Medium | Few-shot examples in analysis prompt. Track false positive rate during calibration. Allow user to flag misclassifications in review. Iterate prompt based on real-world sessions. Accept ~85% accuracy as good enough for MVP1 — the trend matters more than any single count. |
| 7 | **JSON file corruption or data loss.** Crash during write, accidental deletion, manual editing gone wrong. | Low | Critical | Atomic writes (temp + rename). Backup last 3 versions (rotate on write). Warn user if file is missing/corrupted on startup. Include `export` command from Sprint 4 so users can snapshot data. |
| 8 | **ffmpeg not installed or wrong version.** System dependency that varies across platforms. | Medium | Medium | Check for ffmpeg on startup with clear error message and install instructions per platform. Pin minimum ffmpeg version. Consider bundling via `ffmpeg-python` or `static-ffmpeg` pip package. |
| 9 | **Phase transition feels arbitrary or premature.** User hits session count but doesn't feel ready, or metrics game the threshold. | Medium | Medium | Allow user to defer transition ("Stay in Phase 1 for 5 more sessions"). Show transition criteria transparently in `status` command. Require metric thresholds sustained over last 5 sessions (already in PRD), not just hit once. |
| 10 | **Scope creep on MVP1.** PRD is ambitious for 3 engineers in 9 weeks — Phase 3 exercises, hostile Q&A topic generation, and full polish may not all land. | High | Medium | Phase 3 daily rotation and hostile Q&A generation are the highest-risk features to cut. MVP1 is shippable with Phase 1 fully polished + Phase 2 functional + Phase 3 stubbed. Prioritize the daily loop quality over Phase 3 breadth. |
| 11 | **Whisper model download size / first-run experience.** `medium` model is ~1.5GB download. First-run setup may frustrate users. | Medium | Low | Default to `base` model (~150MB) with option to upgrade. Pre-flight check on `practice` command — if model not downloaded, prompt user and show progress. Document model size tradeoffs in README. |
| 12 | **Cross-device portability friction.** User needs to copy JSON file manually between devices. No sync, no cloud. | Medium | Low | Acceptable for MVP1 (CLI-savvy users). Document the portable file path. Consider adding `import`/`export` commands that produce a single transferable archive (JSON + audio). Cloud sync is a GA feature. |

---

## 5. Open Questions for PM / Design / Infra

### For PM

1. **Phase 3 scope in MVP1 — is it a hard requirement?** Phase 3 exercises (hostile Q&A, argue both sides, random word story) add significant implementation surface. If we ship MVP1 with Phase 1 polished + Phase 2 functional + Phase 3 stubbed ("coming soon"), does that still meet the launch bar? This is the single biggest scope lever.

2. **Calibration mode — user-facing or silent?** The PRD mentions a calibration flag for the first ~10 sessions. Should we tell the user "scores may shift as calibration improves" or handle it silently? Recommendation: be transparent — show a small banner for sessions 1-10.

3. **Session skip / rest days?** The PRD tracks streaks but doesn't define what breaks a streak. Is it 1 missed day? 2? Should the tool accommodate planned rest days without streak penalty?

4. **Topic override behavior?** PRD says users can override the topic. When they do, should the tool still assign a framework and focus skills, or let the user go fully freeform? Recommendation: still assign framework (user can ignore it), but note "custom topic" in session data.

### For Design

5. **Terminal output density.** The scorecard + tips + trends + phase progress is a lot of text. Should we paginate (press Enter to continue), use collapsible sections, or dump everything at once? Recommendation: show scorecard + top tip immediately, then prompt "Show full analysis? [y/N]".

6. **Repeat-and-improve flow (Phase 2).** The PRD mentions "2 min + 60-second repeat and improve." Is this two separate recordings analyzed independently, or one session with a before/after comparison? Recommendation: two recordings, second scored against first with explicit delta shown.

### For Infra

7. **CI/CD for the Python package.** Do we want PyPI distribution, or is this installed from source / GitHub? Recommendation: GitHub-only install (`pip install git+...`) for MVP1, PyPI for GA.

8. **Whisper model hosting.** Default Whisper downloads models from Hugging Face on first use. If team machines have network restrictions, do we need to pre-stage models or host them internally?

---

## Appendix: Prompt Architecture Sketch

The analysis prompt is the core IP. High-level structure:

```
SYSTEM: You are a speaking clarity analyst...

CONTEXT:
- User phase: {phase}
- Active metrics: {phase-gated list}
- Assigned framework: {framework_name} with components: {components}
- Focus skills: {skills}
- Session parameters: {duration, prep_time, topic_type}

RUBRIC:
- {5-dimension scoring rubric, only active dimensions}
- {Benchmark tables}

LEXICONS:
- Filler words: {list + disambiguation examples}
- Maze patterns: {definitions + examples}  (Phase 2+)
- Hedging phrases: {list + strategic vs habitual guidance}  (Phase 3)

RECENT HISTORY:
- Last 5 sessions: {metrics array}
- Baseline: {baseline metrics}

TRANSCRIPT:
{full transcript}

WORD TIMESTAMPS:
{timestamp data from Whisper}

OUTPUT FORMAT:
Return JSON matching this schema: {session analysis schema}
```

Temperature: `0` for scoring consistency. Model: `claude-sonnet-4-5-20250929` (cost-effective for structured analysis; upgrade to Opus if quality insufficient).
