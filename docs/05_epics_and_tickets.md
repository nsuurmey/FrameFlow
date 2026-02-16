# Epic & Ticket Scaffolding

## Overview

This document breaks the four milestones (MVP 0 → MVP 1 → MVP 2 → GA) into implementable epics and tickets. Each ticket is sized, has clear acceptance criteria, and declares dependencies. Tickets are ordered within each epic to minimize blocking.

**Sizing key:**
- **S** = < 4 hours
- **M** = 4–8 hours (1 day)
- **L** = 2–3 days
- **XL** = 4–5 days

**Statuses:** `backlog` → `ready` → `in-progress` → `review` → `done`

---

## Milestone 0: MVP 0 — Audio-Only Proof of Concept

> **Validation question:** Can we extract meaningful, repeatable speaking metrics from raw `.webm` audio without any transcription or AI?

### Epic 0.1: Project Bootstrap

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 0.1.1 | Python project scaffolding | S | — | `pyproject.toml` with project metadata, `src/clarity/` package layout, `tests/` directory, `.gitignore`, `requirements.txt` with pinned deps (`pydub`, `librosa`, `matplotlib`, `pandas`, `scipy`, `numpy`). `python -m clarity --help` prints usage. |
| 0.1.2 | Dev tooling setup | S | 0.1.1 | `ruff` linter config, `pytest` runs with `pytest tests/`, `mypy` type-checking passes on empty package. All three runnable via single `make check` or equivalent. |
| 0.1.3 | Test audio fixture | S | — | At least one `.webm` file from Android Recorder committed to `tests/fixtures/`. `ffprobe` output documented (codec, sample rate, channels). A second fixture with known word count for WPM calibration. |

### Epic 0.2: Audio Ingestion Pipeline

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 0.2.1 | `.webm` loading and conversion | M | 0.1.1, 0.1.3 | Function accepts a `.webm` path, returns a `numpy` array + sample rate. Uses `pydub` + `ffmpeg` under the hood. Raises clear error if ffmpeg missing or file corrupt. Unit test passes against fixture. |
| 0.2.2 | ffmpeg dependency check | S | 0.1.1 | On import or CLI entry, check `ffmpeg` is on PATH. If missing, print install instructions for Linux, macOS, and Windows. Test with mock-missing ffmpeg. |
| 0.2.3 | CLI entry point with file argument | S | 0.2.1 | `python -m clarity analyze <file.webm>` loads the file and prints duration to console. `--help` shows usage. Uses `argparse` (no framework dependencies yet). |

### Epic 0.3: Metric Analyzers

Each analyzer is a standalone function: audio array in → metric dict out.

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 0.3.1 | M1 — Duration & speaking time | M | 0.2.1 | Returns `total_duration_s`, `speaking_time_s`, `speaking_ratio`. Uses silence detection to separate speech from non-speech. Unit test: fixture file duration matches `ffprobe` duration ± 0.5s. |
| 0.3.2 | M2 — Pause detection | L | 0.3.1 | Returns `pause_count`, `pauses_per_min`, `mean_pause_s`, `long_pause_count`, `pause_durations[]`, `pause_timestamps[]`. Configurable silence threshold (dBFS) and minimum duration (ms). Unit test: manually counted pauses in fixture match output ± 1. |
| 0.3.3 | M3 — Speaking rate estimation | L | 0.2.1 | Returns `est_syllables_per_min`, `est_wpm`, `rate_variation_sd`. Uses librosa energy envelope peak detection as syllable proxy. WPM = syllables/min ÷ 1.5. Unit test: estimated WPM on known-word-count fixture is within 30% of actual. |
| 0.3.4 | M4 — Energy / volume profile | M | 0.2.1 | Returns `mean_energy`, `energy_variance`, `trailing_off_pct` (energy drop in final 30s vs. first 30s). Unit test: energy values are non-zero floats for valid audio. |
| 0.3.5 | M5 — Pitch tracking (F0) | L | 0.2.1 | Returns `mean_pitch_hz`, `pitch_range_hz`, `pitch_variance`, `uptalk_count`. Uses `librosa.pyin`. Unit test: pitch values within human speech range (75–300 Hz) for fixture. |
| 0.3.6 | Configurable thresholds via CLI args | S | 0.3.1–0.3.5 | CLI accepts `--silence-threshold`, `--min-pause-ms`, `--wpm-target-low`, `--wpm-target-high`. Defaults match PRD values. Values passed through to analyzers. |

### Epic 0.4: Reporting & Visualization

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 0.4.1 | Console report formatter | M | 0.3.1–0.3.5 | Running `clarity analyze <file>` prints the full session report matching the format in the MVP 0 PRD (duration, pauses, rate, energy, pitch sections). Includes rating indicators (checkmark / warning). |
| 0.4.2 | PNG plot generation | L | 0.3.1–0.3.5 | Generates 4 PNGs to an output directory: (1) waveform + pause overlay, (2) energy contour, (3) pitch contour, (4) speaking rate heatmap. `--no-plots` flag to skip. Files render without errors. |
| 0.4.3 | CSV session log | M | 0.4.1 | Each run appends one row to `clarity_log.csv` with all metrics. Creates file with header on first run. Columns match the PRD schema. Test: run 3 times, CSV has 3 data rows + 1 header. |
| 0.4.4 | Session comparison (vs. last) | S | 0.4.3 | If CSV has prior sessions, console report includes a "vs. LAST SESSION" section with directional arrows (↑/↓) and improving/worsening labels. |
| 0.4.5 | Trend line charts | M | 0.4.3 | Generates a trend PNG with line charts for key metrics across all sessions (pause rate, WPM, pitch variance). Only generates if ≥ 2 sessions in CSV. |

### Epic 0.5: MVP 0 Validation & Calibration

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 0.5.1 | Calibration test suite | M | 0.3.1–0.3.5 | Documented calibration run: silence threshold tuning, WPM accuracy check vs. known passage, pitch sanity check. Results recorded in `docs/calibration_results.md`. |
| 0.5.2 | End-to-end smoke test | S | 0.4.1–0.4.5 | Single pytest test: runs full `clarity analyze` on fixture, asserts exit code 0, CSV row written, PNGs created, console output contains all 5 metric sections. |
| 0.5.3 | MVP 0 exit criteria sign-off | S | 0.5.1, 0.5.2 | Checklist verified: (1) script runs E2E on test `.webm`, (2) all 5 metrics produce non-trivial output, (3) CSV appends across 3+ runs, (4) PNGs render, (5) WPM within 30% of known count. |

**MVP 0 total: 19 tickets | ~4–5 weeks solo**

---

## Milestone 1: MVP 1 — Core Daily Practice Loop

> **Validation question:** Can a user complete a full daily practice session (record → transcribe → analyze → feedback) in under 10 minutes with actionable coaching?

### Epic 1.1: CLI Framework & Storage

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.1.1 | Migrate CLI to `typer` + `rich` | M | MVP 0 done | Replace `argparse` with `typer`. Commands: `practice`, `baseline`, `history`, `status`, `review`. Each prints a stub message. `rich` console object initialized. |
| 1.1.2 | JSON storage manager | L | 1.1.1 | `StorageManager` class: init `~/.clarity/clarity_sessions.json` on first run with PRD schema. Atomic writes (temp + rename). Read/write user profile, session list, metrics history. Unit tests for each operation including crash-during-write simulation. |
| 1.1.3 | Config file support | S | 1.1.2 | `~/.clarity/config.json` with keys: `whisper_model` (default `base`), `archive_audio` (default `true`), `anthropic_api_key` (or env var `ANTHROPIC_API_KEY`). CLI reads config on startup. |
| 1.1.4 | First-run setup flow | S | 1.1.2, 1.1.3 | On first run (no JSON exists): create `~/.clarity/` directory, initialize JSON, prompt for API key (or detect env var), download Whisper model if needed with progress bar. |

### Epic 1.2: Audio Pipeline & Transcription

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.2.1 | Whisper integration | L | 1.1.1 | Function: `.webm` path → transcript text + word-level timestamps. Uses `openai-whisper` with configurable model size. Returns structured result with `words[]` (word, start, end). |
| 1.2.2 | Whisper filler fidelity testing | L | 1.2.1 | Test `tiny`, `base`, `small`, `medium` models against recordings with deliberate fillers (um, uh, like, so). Document preservation rate per model. **Blocker**: determines default model choice. Results in `docs/whisper_fidelity.md`. |
| 1.2.3 | Duration & WPM from timestamps | S | 1.2.1 | Calculate `duration_s`, `word_count`, `wpm` from Whisper timestamp data. Map filler positions to speech segments (opening / middle / closing / transitions). |
| 1.2.4 | Transcript paste fallback | M | 1.2.3 | `practice --paste` mode: user pastes transcript text, manually enters duration. Produces same structured result as audio path (minus word timestamps). Shared interface with 1.2.1 output. |
| 1.2.5 | Audio archival | S | 1.1.2, 1.2.1 | Copy uploaded `.webm` to `~/.clarity/audio/session_NNN.webm`. Respect `archive_audio` config toggle. |

### Epic 1.3: Session Setup & Phase System

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.3.1 | Phase configuration data models | M | 1.1.1 | Dataclasses for Phase 1/2/3: active metrics, available frameworks, topic types, prep time, speaking duration, warm-up exercises, transition thresholds. All values match PRD tables. |
| 1.3.2 | Topic pool & rotation | M | 1.3.1 | 15–20 topics per phase. Rotation tracking in storage (no repeats until pool exhausted). Topic override via `--topic "custom topic"`. |
| 1.3.3 | Framework assignment | S | 1.3.1 | Deterministic mapping: topic type → framework (PREP, What-So What-Now What, Problem-Solution-Benefit, STAR, Pyramid). Framework components displayed in session brief. |
| 1.3.4 | Warm-up display | S | 1.3.1 | Phase-specific warm-up exercises rendered with `rich` formatting. Phase 1: tongue twisters + breathing. Phase 2: vocal variety drills. Phase 3: rapid-fire association. |
| 1.3.5 | Focus skill selection | S | 1.3.1, 1.1.2 | Pick 1–2 skills from phase-appropriate pool, weighted toward user's weakest dimensions (from last 5 sessions). Display in session brief. |
| 1.3.6 | Session setup orchestration | M | 1.3.2–1.3.5 | Full setup flow: detect phase → display warm-up → generate topic → assign framework → select focus skills → display session brief with prep timer countdown. |
| 1.3.7 | Baseline session flow | M | 1.3.6, 1.2.1 | First-run detection (no sessions in storage). Runs simplified session: skip warm-up, use standard topic, record baseline metrics. Stored as `baseline` in user profile. |

### Epic 1.4: Analysis Engine (Claude API)

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.4.1 | Claude API client | M | 1.1.3 | Wrapper around `anthropic` SDK. Sends prompt, receives structured JSON. Handles: API errors, timeouts (30s default), rate limits with retry, missing API key with helpful error. |
| 1.4.2 | Analysis prompt v1 | L | 1.3.1 | Full prompt assembly: system message + rubric (5 dimensions) + filler lexicon + framework definitions + few-shot disambiguation examples. Phase-gated: only include active dimensions. Test against 3–5 hand-crafted transcripts. |
| 1.4.3 | Analysis prompt v2 (calibration) | L | 1.4.2 | Iterate prompt based on v1 results. Add maze detection rubric, hedging lexicon. Calibrate scoring against 10+ transcripts with expected scores. Scoring variance < ±5 points on same transcript across 5 runs (temperature=0). |
| 1.4.4 | Phase-gated prompt assembly | M | 1.4.2, 1.3.1 | Dynamic prompt builder: Phase 1 = filler focus + PREP framework only. Phase 2 = add maze/hedge + framework rotation. Phase 3 = full rubric + pressure context. Injects last-5-session metrics and baseline. |
| 1.4.5 | Structured output parsing | M | 1.4.1 | Parse Claude's JSON response into session analysis dataclass. Validate all required fields present. Graceful fallback if response is malformed (retry once, then surface raw text). |

### Epic 1.5: Feedback & Scoring

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.5.1 | Scorecard renderer | M | 1.4.5 | `rich` table: dimension names, scores (0–100), benchmark ratings (Developing/Competent/Strong/Excellent), composite score with weights. Phase-gated: only show active dimensions. Color-coded (red < 50, yellow 50–74, green ≥ 75). |
| 1.5.2 | Tip formatter | M | 1.4.5 | Display 3 actionable tips from Claude response. Each tip: title, explanation, transcript excerpt (highlighted), technique reference. Numbered and formatted with `rich` panels. |
| 1.5.3 | Trend comparator | M | 1.1.2, 1.4.5 | Show current session vs. average of last 5 sessions. Show current vs. baseline. Directional arrows + delta values. "Personal best" callouts when a dimension hits a new high. |
| 1.5.4 | Phase milestone tracker | S | 1.1.2, 1.3.1 | Display in scorecard footer: sessions completed in current phase, sessions remaining, metric gaps to next phase threshold. "Phase 2 unlocks in N sessions if you maintain X." |
| 1.5.5 | Overcorrection detector | S | 1.4.5, 1.1.2 | If filler rate = 0 for 3+ consecutive sessions, flag in tips: "Watch for over-monitoring — some fillers are natural." |
| 1.5.6 | Comfort rating input | S | 1.4.5 | Post-session prompt: "How comfortable did you feel? (1–10)". Stored in session data. Used as vocal delivery proxy until MVP 2 audio scoring. |

### Epic 1.6: Session Orchestrator

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.6.1 | `practice` command — full workflow | L | 1.3.6, 1.2.1, 1.4.1, 1.5.1–1.5.4, 1.1.2 | Coordinates: setup → warm-up → prompt to record → accept `.webm` path → transcribe (with progress) → analyze (with spinner) → display scorecard + tips + trends → persist session. Entire flow < 10 min wall clock. |
| 1.6.2 | `baseline` command | S | 1.3.7, 1.6.1 | Runs baseline flow. Errors if baseline already exists (offer `--force` to re-record). |
| 1.6.3 | `history` command | M | 1.1.2 | `rich` table of last N sessions (default 10): date, topic, composite score, phase, streak. `--all` flag for full list. |
| 1.6.4 | `review <id>` command | M | 1.1.2 | Re-display full scorecard + tips for a past session by ID. |
| 1.6.5 | `status` command | S | 1.1.2, 1.3.1 | Current phase, day count, streak, next session targets, phase transition progress bar. |
| 1.6.6 | `weekly` command | M | 1.1.2 | Aggregate metrics for current week: sessions completed, average scores, best/worst dimensions, streak status. |
| 1.6.7 | Phase transition logic | M | 1.1.2, 1.3.1 | After each session: evaluate transition thresholds (session count + metrics sustained over last 5). If met, prompt user to advance or defer. Record transition in storage. |

### Epic 1.7: Phase 2 & 3 Exercises

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.7.1 | Phase 2 topic pool & exercises | M | 1.3.1, 1.3.2 | Persuasive topics, Feynman drill prompts. Framework rotation (all 5 frameworks available). 10s prep time, 2-min speaking duration. |
| 1.7.2 | Repeat-and-improve flow | L | 1.6.1 | Phase 2 special mode: two recordings per session. Second scored against first with explicit delta. Prompt structure: "Now do it again in 60 seconds — focus on [weakest dimension]." |
| 1.7.3 | Phase 3 daily rotation | M | 1.3.1, 1.6.1 | Day-of-week schedule: Mon = zero-prep, Tue = hostile Q&A topics, Wed = argue both sides, Thu = framework blitz, Fri = random word story. |
| 1.7.4 | Phase 3 exercise types | L | 1.7.3, 1.4.2 | Implement each exercise type: hostile Q&A topic generation, argue-both-sides prompt, random-word story prompt, framework blitz (3 frameworks in one session). Analysis prompt adapts per exercise type. |

### Epic 1.8: Hardening & Polish

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 1.8.1 | Error handling hardening | M | 1.6.1 | Graceful handling: ffmpeg missing, Whisper download failure, corrupted `.webm`, API timeout, malformed JSON, disk full. Each error shows actionable message. |
| 1.8.2 | End-to-end test suite | L | 1.6.1 | Pytest tests simulating full 5-session arc through Phase 1 with mocked Whisper + Claude. Asserts: sessions stored, scores computed, trends calculated, no crashes. |
| 1.8.3 | Performance validation | M | 1.6.1 | Measure and document: Whisper transcription time by model, Claude API latency, total wall clock per session. Confirm < 10 min target. Results in `docs/performance.md`. |
| 1.8.4 | README & install guide | M | 1.8.1 | Setup instructions: Python version, ffmpeg install (per platform), Whisper model download, API key config, first-run walkthrough. Quick start in < 5 min. |

**MVP 1 total: 39 tickets | ~10–14 weeks solo, ~5–7 weeks with 2–3 contributors**

---

## Milestone 2: MVP 2 — Audio-Enhanced Analysis & Export

> **Validation question:** Can we combine transcript-based and audio-based metrics into a richer feedback loop, and make results portable?

### Epic 2.1: Audio-Derived Vocal Scoring

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 2.1.1 | Integrate MVP 0 analyzers into MVP 1 pipeline | L | MVP 1 done | Pitch, energy, and pause analyzers from MVP 0 run alongside Whisper transcription. Results passed to analysis engine as additional context. |
| 2.1.2 | Vocal delivery score from audio | L | 2.1.1 | Replace self-rating (comfort score) with computed vocal delivery score: weighted combination of pitch variance, energy dynamics, and pause quality. Calibrate weights against user self-ratings from MVP 1 sessions. Target: ±15 points of self-rating. |
| 2.1.3 | Pause quality scoring | M | 2.1.1 | Combine Whisper timestamp gaps with audio pause detection. Score pause placement (at clause boundaries = good) using transcript structure. |

### Epic 2.2: Format Expansion

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 2.2.1 | Multi-format audio support | M | MVP 1 done | Accept `.mp3`, `.wav`, `.m4a` in addition to `.webm`. Auto-detect format via ffprobe. Conversion pipeline generalized. |
| 2.2.2 | Transcript file import | M | MVP 1 done | `practice --transcript <file.txt>` imports transcript from file. Supports `.txt` and `.md`. Normalizes whitespace and formatting. Manual duration input. |

### Epic 2.3: Export & Reporting

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 2.3.1 | Markdown session report export | L | MVP 1 done | `review <id> --export` generates a `.md` file with full scorecard, tips, transcript excerpts, and trend charts (inline sparklines or linked PNGs). |
| 2.3.2 | Bulk export command | M | 2.3.1 | `export --format md --range last-30` exports a summary report covering N sessions. Includes aggregate stats and dimension-by-dimension trends. |
| 2.3.3 | CSV/JSON metrics export | S | MVP 1 done | `export --format csv` and `export --format json` for raw metrics. Enables external charting and analysis. |

**MVP 2 total: 8 tickets | ~4–6 weeks**

---

## Milestone 3: GA — Full Platform

> **Validation question:** Is this a complete, polished daily speaking coach that a user would recommend to a colleague?

### Epic 3.1: In-CLI Recording

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 3.1.1 | Audio recording via `sounddevice` | L | MVP 2 done | `practice --record` starts recording directly in CLI. Visual level meter during recording. Stop with Enter or after max duration. Saves `.wav` to `~/.clarity/audio/`. |
| 3.1.2 | Recording quality validation | M | 3.1.1 | Post-recording check: sample rate ≥ 16kHz, signal-to-noise ratio acceptable, duration within expected range. Warn user if quality is low. |

### Epic 3.2: Live Claude Interaction

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 3.2.1 | Streaming Q&A follow-up | L | MVP 2 done | After scorecard display, user can ask follow-up questions about their session. Claude responds with streaming output. Context includes full session analysis. |
| 3.2.2 | Live hostile Q&A mode | XL | 3.2.1 | Phase 3 exercise: Claude generates challenging questions in real-time. User records responses. Multi-turn interaction: question → record → analyze → next question. 3–5 rounds per session. |

### Epic 3.3: Comparison & Custom Content

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 3.3.1 | Side-by-side session comparison | M | MVP 2 done | `compare <id1> <id2>` displays two sessions in parallel columns. Highlights dimension-by-dimension deltas. Works across phases. |
| 3.3.2 | Custom topic libraries | M | MVP 2 done | `topics add "My custom topic" --phase 2 --type persuasive`. User-defined topics stored in config. Mixed into rotation alongside built-in pool. |
| 3.3.3 | 30/60/90-day milestone reports | L | MVP 2 done | Auto-generated comprehensive report at phase transitions. Full baseline comparison, best sessions, dimension growth curves, streak stats, phase-specific insights. |

### Epic 3.4: Integration & Polish

| ID | Ticket | Size | Depends On | Acceptance Criteria |
|----|--------|------|------------|---------------------|
| 3.4.1 | Calendar/reminder integration | M | MVP 2 done | `remind set 08:00` configures daily system notification. Supports cron (Linux/macOS). Shows streak-at-risk warning if no session by set time. |
| 3.4.2 | Full 90-day program E2E test | L | All GA epics | Simulated 90-day progression with test data. All phase transitions, exercise types, milestone reports, and edge cases verified. |
| 3.4.3 | Comprehensive documentation | M | All GA epics | Full README: install, quickstart, command reference, FAQ, troubleshooting. All commands documented with examples. |

**GA total: 11 tickets | ~8–12 weeks**

---

## Dependency Graph (Cross-Epic)

```
MVP 0                          MVP 1                              MVP 2           GA
─────                          ─────                              ─────           ──

0.1 Bootstrap ──┐
                ├─► 0.2 Ingestion ──┐
0.1.3 Fixture ──┘                   │
                                    ├─► 0.3 Analyzers ──┐
                                    │                    ├─► 0.4 Reporting ──► 0.5 Validation
                                    │                    │
                                    │                    │         ┌─► 2.1 Vocal scoring
                                    │                    │         │
                                    │                    └─────────┘
                                    │
                         MVP 0 done ╪══════════════════════════════════════════════
                                    │
                   1.1 CLI+Storage ─┤
                                    ├─► 1.2 Transcription ──┐
                   1.3 Phase system ┤                       │
                                    ├─► 1.4 Analysis ───────┤
                                    │                       ├─► 1.6 Orchestrator ──► 1.8 Hardening
                                    └─► 1.5 Feedback ───────┘         │
                                                                      ├─► 1.7 Phase 2/3
                                                                      │
                                                           MVP 1 done ╪═══════════
                                                                      │
                                                          2.1 Vocal ──┤
                                                          2.2 Format ─┤
                                                          2.3 Export ──┤
                                                                      │
                                                           MVP 2 done ╪═══════════
                                                                      │
                                                        3.1 Recording ┤
                                                        3.2 Live Q&A ─┤
                                                        3.3 Compare ──┤
                                                        3.4 Polish ───┘
```

---

## Ticket Summary

| Milestone | Epics | Tickets | Est. Solo Duration |
|-----------|-------|---------|-------------------|
| MVP 0 | 5 | 19 | 4–5 weeks |
| MVP 1 | 8 | 39 | 10–14 weeks |
| MVP 2 | 3 | 8 | 4–6 weeks |
| GA | 4 | 11 | 8–12 weeks |
| **Total** | **20** | **77** | **26–37 weeks** |

---

## Implementation Order (Recommended)

For a solo developer, the recommended attack order within each milestone:

### MVP 0 (first 4–5 weeks)
1. 0.1.1 → 0.1.2 → 0.1.3 (bootstrap — day 1–2)
2. 0.2.1 → 0.2.2 → 0.2.3 (ingestion — day 3–5)
3. 0.3.1 → 0.3.2 (duration + pauses — highest value first)
4. 0.3.3 (speaking rate — the key validation metric)
5. 0.3.4 → 0.3.5 → 0.3.6 (energy, pitch, config)
6. 0.4.1 → 0.4.3 → 0.4.4 (console report + CSV — usable output)
7. 0.4.2 → 0.4.5 (plots — nice to have but lower priority)
8. 0.5.1 → 0.5.2 → 0.5.3 (validation — exit criteria)

### MVP 1 (next 10–14 weeks)
1. 1.1.1 → 1.1.2 → 1.1.3 → 1.1.4 (CLI + storage foundation)
2. 1.2.1 → 1.2.2 (Whisper — blocker on model choice)
3. 1.3.1 → 1.3.2 → 1.3.3 → 1.3.4 → 1.3.5 (phase system)
4. 1.4.1 → 1.4.2 (Claude integration + prompt v1)
5. 1.2.3 → 1.2.4 → 1.2.5 (remaining audio pipeline)
6. 1.3.6 → 1.3.7 (session setup orchestration)
7. 1.4.3 → 1.4.4 → 1.4.5 (prompt calibration + parsing)
8. 1.5.1 → 1.5.2 → 1.5.3 → 1.5.4 → 1.5.5 → 1.5.6 (feedback)
9. 1.6.1 → 1.6.2 → 1.6.3 → 1.6.4 → 1.6.5 → 1.6.6 → 1.6.7 (commands + transitions)
10. 1.7.1 → 1.7.2 → 1.7.3 → 1.7.4 (Phase 2/3 — can be deferred)
11. 1.8.1 → 1.8.2 → 1.8.3 → 1.8.4 (hardening + docs)
