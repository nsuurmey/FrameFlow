# PRD: Speaking Clarity Practice Tool (v2 — Research-Informed)

## Overview

A CLI-based daily speaking practice tool built with Claude Code that guides users through structured practice sessions, analyzes transcripts for clarity metrics, provides actionable feedback, and tracks progress over time.

**Core Philosophy:** 10 minutes a day, measurable progress, portable across devices.

**Foundational Model (from research):** Speaking fluency is downstream of cognitive organization. The tool targets the Conceptualizer stage of Levelt's speech production pipeline — structured thinking frameworks reduce cognitive load, freeing working memory for fluent formulation and dynamic delivery. The tool improves *thinking*, which produces better *speaking*.

---

## Problem Statement

Improving speaking clarity (reducing filler words, improving structure, sharpening thought-to-speech translation) requires consistent practice with feedback loops. Current options are either too heavyweight (Toastmasters, coaching), too passive (watching TED talks), or too expensive (1:1 speech coaching). Existing AI tools (Yoodli, Poised, Orai) focus on real-time coaching or gamified lessons but don't combine structured daily practice regimens with transcript-level analysis and long-arc progress tracking.

---

## User Persona

- Technical professional who communicates complex ideas to varied audiences
- Already articulate but wants to sharpen: reduce fillers, improve extemporaneous structure, increase clarity under pressure
- Has ~10 min/day for practice
- Works across multiple devices (mobile, Chromebook, desktop)
- Comfortable with CLI tools and transcript-based workflows

---

## MVP 1 Scope

### Input Methods
1. **Upload .webm audio file** — recorded directly from the Android Recorder app. This is the primary input method and provides ground truth audio: raw, unprocessed, with all fillers, pauses, and disfluencies preserved. The tool handles transcription internally.
2. **Paste transcript** (fallback) — user copies transcript text directly into the tool for cases where audio upload isn't practical.

> **Why .webm from Android Recorder:** Advanced transcription tools (Whisper Flow, Granola, Otter.ai) may clean up fillers and disfluencies during transcription, destroying the exact signal we need to measure. The Android Recorder app produces raw .webm files with no post-processing, ensuring ground truth fidelity.
> 
> **Deferred to MVP 2:** Support for additional audio formats (mp3, wav, m4a), Whisper Flow / Granola transcript import, and transcript file upload (txt, md).

### Core Workflow

```
┌─────────────────────────────────────────────────┐
│  1. SESSION SETUP (phase-aware)                 │
│     - Determine user's current phase (1/2/3)    │
│     - Suggest warm-up exercises for phase        │
│     - Generate topic + matched framework         │
│     - Identify 1-2 focus skills for phase        │
│     - Set difficulty parameters                  │
│     - User sees full session brief               │
├─────────────────────────────────────────────────┤
│  2. WARM-UP (guided, external)                  │
│     - Display phase-appropriate warm-up          │
│     - User performs breathing + vocal exercises   │
├─────────────────────────────────────────────────┤
│  3. PRACTICE (external)                         │
│     - User records on Android Recorder app       │
│     - Produces .webm audio file                  │
├─────────────────────────────────────────────────┤
│  4. AUDIO INPUT & TRANSCRIPTION                 │
│     - Upload .webm file                          │
│     - OR paste transcript (fallback)             │
│     - Tool transcribes audio via Whisper         │
│     - Raw transcript preserved (no cleanup)      │
│     - Duration auto-extracted from audio          │
├─────────────────────────────────────────────────┤
│  5. ANALYSIS (Claude — phase-aware)             │
│     - Filler word detection & count              │
│     - Maze / false start detection               │
│     - Hedging language detection                 │
│     - Framework completion check                 │
│     - Phase-appropriate metrics only             │
│     - 5-dimension weighted scoring               │
├─────────────────────────────────────────────────┤
│  6. FEEDBACK & TIPS                             │
│     - Session scorecard (phase-appropriate)      │
│     - Top 3 actionable tips                      │
│     - Comparison to previous sessions            │
│     - Phase milestone progress                   │
├─────────────────────────────────────────────────┤
│  7. STORAGE                                     │
│     - Session data saved to local JSON           │
│     - Phase progression updated                  │
│     - Metrics history appended                   │
└─────────────────────────────────────────────────┘
```

---

## The 30/60/90-Day Phase Model

The tool operates in three progressive phases derived from the research regimen. Phase determines everything: which metrics are tracked, which frameworks are practiced, topic difficulty, prep time allowed, and scoring thresholds.

### Phase 1: Foundation (Days 1–30) — Awareness & Structure

**Goals:** Build filler awareness (don't eliminate — just count). Master the PREP framework. Replace fillers with pauses by end of phase.

**Metrics tracked:** Filler rate (per min), filler % of total words, framework completion (Y/N), subjective comfort (1–10)

**Frameworks practiced:** PREP only (weeks 1–2), PREP + What–So What–Now What (weeks 3–4)

**Topic types:** Explain a concept you know well, teach something to a non-expert, describe a recent decision

**Prep time:** 60 seconds silent planning (weeks 1–2), 30 seconds (weeks 3–4)

**Speaking duration:** 60–90 seconds

**Warm-up:** Box breathing (4-4-4-4, 3 cycles) → lip trills → tongue twister (slow then fast) → read one sentence aloud slowly

**Success indicator:** User catches themselves *before* saying "um." Can reliably hit all PREP components in 60 seconds. 50%+ reduction in filler rate from baseline.

### Phase 2: Development (Days 31–60) — Complexity & Flow

**Goals:** Vocal variety. Strategic pausing. Framework rotation. Increase topic complexity.

**New metrics added:** Speaking rate (WPM), false starts / mazes per minute, sentence completion rate

**Frameworks practiced:** Rotate among PREP, What–So What–Now What, Problem–Solution–Benefit, Past–Present–Future (matched to topic type)

**Topic types:** Add persuasive arguments, trend analysis, Feynman drill (explain to a 5-year-old — no jargon permitted)

**Prep time:** 10 seconds (user must choose framework quickly)

**Speaking duration:** 2 minutes + 60-second "repeat and improve"

**Warm-up:** Diaphragmatic breathing → vocal sirens → tongue twister at max clean speed → consonant-vowel drill

**Success indicator:** Naturally leads with main point (BLUF). Structural frameworks feel automatic. Deliberate pace variation.

### Phase 3: Integration (Days 61–90) — Pressure & Polish

**Goals:** Handle zero-prep scenarios. Cognitive flexibility under pressure. Delivery polish.

**New metrics added:** Pause quality (% at syntactic boundaries), vocal variety (subjective), hedging frequency, key message delivery

**Frameworks:** All frameworks available, speaker selects in real-time

**Topic types:** Add hostile Q&A simulation (Claude generates challenging questions), argue both sides (60s FOR / 60s AGAINST), story from three random words, no-prep 3-minute speech

**Prep time:** Zero for capstone exercises

**Speaking duration:** 2–3 minutes

**Warm-up:** Abbreviated — box breathing (4 cycles) + one tongue twister at speed

**Daily rotation (Phase 3):**
- Monday: 3-minute persuasive speech (hook → problem → solution → vision → CTA)
- Tuesday: Hostile Q&A (5 AI-generated questions, 30–60 sec each)
- Wednesday: Argue both sides (60s FOR, 60s AGAINST)
- Thursday: Story from 3 random words (2 min, clear beginning/middle/end)
- Friday: No-prep 3-minute speech (zero preparation, the capstone)

**Success indicator:** Coherent 3-minute response on any topic with zero prep. Filler rate consistently ≤2/min. WPM in 130–160 range with deliberate variation.

### Phase Transitions

Phase advances are based on session count AND metric thresholds, not calendar time alone:

- **Phase 1 → 2:** ≥20 sessions completed AND filler rate ≤5/min for last 5 sessions AND framework completion >80%
- **Phase 2 → 3:** ≥20 sessions in Phase 2 AND filler rate ≤3/min AND maze rate <2/min AND sentence completion >90%
- **Phase 3 → Maintenance:** After 90-day arc complete, tool enters maintenance mode with full exercise rotation and all metrics active

---

## Feature Requirements

### F1: Session Setup & Prompting (Phase-Aware)

The tool generates a session brief that includes:

- **Warm-up prompt:** Phase-specific exercises displayed as instructions (user performs externally). See phase definitions above.

- **Topic prompt:** A subject matched to the user's current phase. Topic types increase in complexity across phases:
  - Phase 1: Explain, teach, describe (familiar territory)
  - Phase 2: Persuade, analyze trends, Feynman drill (increasing cognitive load)
  - Phase 3: Hostile Q&A, argue both sides, random word story, zero-prep (maximum pressure)

- **Framework assignment:** The tool assigns a specific structural framework based on topic type:
  - Opinions/arguments → PREP
  - Information/updates → What–So What–Now What
  - Proposals/pitches → Problem–Solution–Benefit
  - Experience-based → STAR
  - Complex technical → Pyramid Principle (Phase 2+)
  - Phase 3: User selects their own framework in ≤10 seconds

- **Focus skills (1-2 per session):** Phase-appropriate, drawn from:
  - Phase 1: Filler awareness, framework adherence
  - Phase 2: Filler reduction (active replacement), vocal variety, strategic pausing, pacing control
  - Phase 3: Conciseness, hedging elimination, cognitive flexibility, strong openings/closings

- **Session parameters:**
  - Speaking duration (phase-dependent: 60s → 2min → 3min)
  - Prep time allowed (phase-dependent: 60s → 10s → 0s)
  - Difficulty level (encoded as topic complexity + prep time + duration)

**Topic selection logic:**
- Rotate across topic types within the phase
- Allow user override ("I want to talk about X instead")
- Weight toward areas where metrics show room for improvement
- Phase 3: Support daily rotation schedule (Mon–Fri variety)

### F2: Transcript Analysis Engine (Phase-Aware)

Claude analyzes the transcript using **only the metrics active for the user's current phase.** This prevents cognitive overload — the same principle the research applies to speaking improvement applies to feedback design.

#### Filler Word Analysis (ALL PHASES — HIGH PRIORITY)

- **Detection:** Identify all filler words/phrases: um, uh, ah, like, you know, so, right, basically, actually, I mean, well (when used as filler)
- **Count:** Total fillers
- **Rate:** Fillers per minute (duration auto-extracted from .webm audio; manually input for paste fallback)
- **Percentage:** Fillers as % of total words (credibility threshold: 3% = damaging, per research)
- **Mapping:** Show where in the transcript fillers cluster (opening, transitions, complex passages). Research confirms fillers cluster at utterance beginnings and major discourse boundaries.
- **Trend:** Compare to previous sessions

**Benchmarks (from research):**
| Rating | Fillers/min | % of words |
|--------|------------|------------|
| Excellent | ≤2 | <1% |
| Professional | ≤5 | <3% |
| Needs work | >10 | >5% |

**Important nuance (from research):** The target is calibrated control, not elimination. Zero fillers sounds robotic. 1–2/min is optimal. The tool should flag overcorrection if filler rate drops to 0 for multiple sessions.

#### Maze / False Start Detection (PHASE 2+)

Mazes are distinct from fillers and *more damaging to listener comprehension* (per research). A maze is a verbal dead end where the speaker starts a sentence, realizes the grammatical path is invalid, stops, and restarts.

- **Detection:** Identify false starts, abandoned sentences, restart patterns ("So what I mean is... what I'm trying to say is..."), mid-sentence pivots
- **Count:** Mazes per minute
- **Examples:** Pull specific maze instances from transcript for feedback

**Benchmarks:**
| Rating | Mazes/min |
|--------|----------|
| Good | <1 |
| Acceptable | 1–2 |
| Needs work | >3 |

#### Hedging Language Detection (PHASE 3)

Hedging is distinct from fillers — it signals credibility erosion rather than cognitive lag. Particularly acute for technical professionals presenting findings.

- **Detection:** "I think," "maybe," "sort of," "kind of," "I guess," "probably," "it seems like," "I feel like"
- **Classification:** Distinguish strategic hedging (appropriate tentativeness on uncertain claims) from habitual hedging (reflexive qualification of known facts)
- **Count:** Hedges per minute and as % of sentences containing hedges

**Benchmark:** Rare/strategic use = good. Present in >20% of sentences = habitual and needs attention.

#### Framework Completion Check (ALL PHASES)

- **Did the speaker hit all components of the assigned framework?**
  - PREP: Point stated? Reason given? Example provided? Point restated?
  - What–So What–Now What: Information presented? Relevance explained? Action specified?
  - Problem–Solution–Benefit: Problem named? Solution presented? Benefit articulated?
- **Score:** Complete / Mostly complete / Structure collapsed
- **Specific feedback:** Which component was weakest or missing

#### Structural Analysis (ALL PHASES)

- Does the response have a clear opening/thesis? (BLUF — Bottom Line Up Front)
- Is there logical flow between ideas?
- Does it reach a conclusion or just trail off?
- Are transitions between ideas explicit or implied?
- Are transitions filler-free? (Research: fillers cluster at transition points)

#### Clarity Metrics

- **Sentence completion rate (Phase 2+):** % of sentences that are grammatically/logically complete. Target: >95%.
- **Topic coherence (All phases):** Does the speaker stay on-topic or drift?
- **Conciseness score (Phase 3):** Signal-to-noise ratio — substantive content vs. filler, repetition, and circumlocution
- **Vocabulary precision (Phase 3):** Use of specific vs. vague language. Jargon appropriateness for stated audience.

### F3: Feedback & Tips (Phase-Aware)

After analysis, present:

**1. Session Scorecard**

Uses the research-derived 5-dimension weighted rubric. Each dimension scored 1–5:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Message Clarity | 30% | Could a listener outline your argument after one hearing? Clear thesis, logical support, decisive conclusion. |
| Fluency | 20% | Filler rate, maze rate, smooth flow. |
| Pacing & Pauses | 20% | Varied rate, strategic pauses at boundaries, comfortable silence. |
| Vocal Delivery | 15% | Varied pitch, volume, emphasis. Conversational and engaging. (Limited in transcript-only MVP — see open questions.) |
| Language Precision | 15% | Sentence completion, vocabulary calibration, hedging frequency. |

**Composite score:** Weighted average × 20 = 0–100 scale.

**Phase-gating:** Only score dimensions the user is actively tracking. In Phase 1, score Message Clarity + Fluency only (50% of total). Expand to full rubric by Phase 3.

**Individual metrics display:**
- Phase 1: Filler rate, filler %, framework completion, comfort rating
- Phase 2: Add WPM, maze rate, sentence completion rate
- Phase 3: Add hedging frequency, pause quality (if detectable), vocal variety (self-rated)

**2. Top 3 Tips**
- Specific, actionable, tied to transcript examples (with quoted excerpts)
- Prioritized by impact within the user's current phase focus
- At least one "quick win" and one "stretch goal"
- Reference specific techniques from the research (e.g., "Try the Three-Pass Pause: close your mouth, breathe, then continue")

**3. Progress Context**
- "Your filler rate dropped from 8.2/min to 6.1/min over the last 5 sessions"
- "You've improved most in: [dimension]. Next focus area: [dimension]"
- Phase milestone progress: "You're 14/20 sessions into Phase 1. Filler rate target for Phase 2: ≤5/min (you're at 6.3)"
- Streaks and consistency tracking
- Periodic baseline comparison: "vs. your Day 1 baseline: filler rate down 62%, framework completion up from 40% to 90%"

### F4: Local Data Storage

All session data stored in a single local JSON file (`clarity_sessions.json`):

```json
{
  "user_profile": {
    "created_at": "2026-02-15",
    "current_phase": 1,
    "phase_start_date": "2026-02-15",
    "total_sessions": 12,
    "current_streak": 5,
    "longest_streak": 8,
    "baseline": {
      "date": "2026-02-15",
      "filler_rate_per_min": 9.4,
      "filler_pct_of_words": 4.2,
      "maze_rate_per_min": 2.1,
      "framework_completion": false,
      "overall_score": 42
    }
  },
  "sessions": [
    {
      "id": "session_012",
      "date": "2026-02-27T08:30:00Z",
      "phase": 1,
      "topic": "Explain the value of Bayesian thinking to a PM",
      "topic_type": "explain_concept",
      "framework_assigned": "PREP",
      "focus_skills": ["filler_awareness", "framework_adherence"],
      "duration_seconds": 90,
      "prep_time_seconds": 60,
      "word_count": 210,
      "input_method": "webm_upload",
      "audio_file": "session_012.webm",
      "transcript": "...",
      "analysis": {
        "composite_score": 64,
        "dimensions": {
          "message_clarity": {"score": 4, "weight": 0.30},
          "fluency": {"score": 3, "weight": 0.20},
          "pacing_pauses": {"score": null, "weight": 0.20, "note": "Not scored in Phase 1"},
          "vocal_delivery": {"score": null, "weight": 0.15, "note": "Not scored in Phase 1"},
          "language_precision": {"score": null, "weight": 0.15, "note": "Not scored in Phase 1"}
        },
        "filler_analysis": {
          "total_count": 7,
          "rate_per_min": 4.67,
          "pct_of_words": 3.3,
          "breakdown": {"um": 3, "uh": 1, "you know": 2, "like": 1},
          "cluster_locations": ["opening (3 fillers in first 15 words)", "transition to example (2 fillers)"],
          "benchmark_rating": "professional"
        },
        "maze_analysis": {
          "total_count": null,
          "rate_per_min": null,
          "note": "Not tracked in Phase 1"
        },
        "hedging_analysis": {
          "total_count": null,
          "note": "Not tracked until Phase 3"
        },
        "framework_completion": {
          "framework": "PREP",
          "point_stated": true,
          "reason_given": true,
          "example_provided": true,
          "point_restated": false,
          "score": "mostly_complete",
          "note": "Missed the restatement — trailed off after the example."
        },
        "sentence_completion_rate": null,
        "wpm": 147,
        "comfort_rating": 6
      },
      "tips": [
        "You clustered 3 fillers in your opening 15 words. Try the Three-Pass Pause before your first sentence: close your mouth, take a breath, then begin.",
        "Your PREP structure was solid through Point → Reason → Example, but you trailed off instead of restating your point. Even a single sentence landing ('That's why Bayesian thinking matters for PMs') closes the loop.",
        "Filler rate of 4.67/min puts you in the professional range — you're already below the credibility cliff of 5/min. Next target: get below 3/min."
      ]
    }
  ],
  "metrics_history": {
    "filler_rate": [9.4, 8.2, 7.1, 6.5, 5.9, 4.67],
    "filler_pct": [4.2, 3.9, 3.5, 3.2, 2.9, 3.3],
    "framework_completion": [false, false, true, true, true, true],
    "composite_score": [42, 48, 55, 58, 62, 64],
    "maze_rate": [null, null, null, null, null, null],
    "wpm": [null, null, null, null, null, null],
    "hedging_rate": [null, null, null, null, null, null],
    "dates": ["2026-02-15", "2026-02-17", "2026-02-19", "2026-02-21", "2026-02-23", "2026-02-27"],
    "phases": [1, 1, 1, 1, 1, 1]
  },
  "phase_transitions": [
    {
      "from": 0,
      "to": 1,
      "date": "2026-02-15",
      "baseline_recorded": true
    }
  ]
}
```

**Storage requirements:**
- Single file, human-readable JSON
- Portable — user can copy between devices
- No external database dependencies
- Include full transcript for re-analysis if needed
- Phase transition history for long-arc tracking
- Null values for metrics not yet active (don't backfill — keeps data honest)

### F5: Session History & Review

User can:
- View summary of last N sessions
- See trend lines (text-based in CLI, or export data for charting)
- Review a specific past session's full analysis
- Get a "weekly summary" of progress within current phase
- Compare current metrics to Day 1 baseline on demand
- View phase transition history and criteria remaining

### F6: Baseline Recording

On first run, the tool prompts the user to complete a baseline session:
- Impromptu 2-minute speech on any topic
- Full analysis with all metrics (regardless of phase) — stored as `baseline` in user_profile
- This baseline is used for comparison at Day 30, 60, and 90 milestones
- User can optionally re-record baseline if first attempt feels unrepresentative

---

## Difficulty Progression Model

Five axes progress across the 90-day arc (from research):

| Axis | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| **Time pressure** | 60s prep | 10s prep | 0s prep |
| **Topic complexity** | Familiar concepts | Abstract/persuasive | Adversarial/impromptu |
| **Structural demand** | Single framework (PREP) | Rotating frameworks | Speaker selects in real-time |
| **Audience pressure** | Solo recording | AI feedback | Simulated hostile Q&A |
| **Duration** | 60–90 seconds | 2 min + repeat | 2–3 minutes |

---

## Analysis Prompt Design

The analysis prompt sent to Claude is the core IP of this tool. It must:

1. **Include the full scoring rubric** with dimension definitions, weights, and benchmarks
2. **Specify the user's current phase** so Claude only scores active metrics
3. **Include the assigned framework** so Claude can check component completion
4. **Include recent metrics history** (last 5 sessions) for trend comparison
5. **Request structured JSON output** matching the session schema above
6. **Include the filler word lexicon** with guidance on distinguishing filler use from meaningful use (e.g., "well" as a filler vs. "well" as a qualifier; "like" as a filler vs. "like" as a comparison)
7. **Include the maze detection rubric** — false starts, abandoned sentences, restart patterns
8. **Include the hedging word lexicon** with guidance on strategic vs. habitual hedging
9. **Reference specific techniques** for tip generation (e.g., Three-Pass Pause, Feynman drill, BLUF)

The prompt should produce consistent, calibrated output — the same transcript analyzed twice should yield very similar scores.

---

## Technical Architecture

### Stack
- **Runtime:** Node.js or Python (Claude Code compatible)
- **Transcription:** OpenAI Whisper (local, open-source) — runs on the .webm audio to produce raw transcripts with filler words and timing data preserved. Whisper's word-level timestamps enable automatic duration calculation, WPM, and filler clustering analysis.
- **AI:** Anthropic API (Claude) for transcript analysis and session generation
- **Storage:** Local JSON file
- **Interface:** CLI (terminal-based)
- **Input:** .webm file reader + stdin for paste fallback
- **Audio processing:** ffmpeg (if needed for .webm → wav conversion pre-Whisper)

### Key Design Decisions
- **Raw transcription:** Whisper is configured to preserve disfluencies (no post-processing cleanup). This is critical — the transcription must include every "um," "uh," and false start.
- **Auto-extracted duration:** Session duration and WPM are calculated from the audio file metadata / Whisper timestamps, removing manual input friction.
- **Word-level timestamps:** Whisper's timestamp output enables filler clustering analysis (where in the speech do fillers concentrate?) and potentially rough pause detection (gaps between word timestamps).
- **Stateless analysis:** Each transcript analysis is a standalone Claude API call with full context (phase config + scoring rubric + transcript + recent metrics history)
- **Prompt engineering:** The analysis prompt is the core IP — it includes the full rubric, benchmarks, filler/maze/hedge lexicons, and framework definitions
- **Offline-capable:** Once the session JSON exists, historical review doesn't require API calls
- **Phase-gating:** The tool enforces progressive complexity — it won't let a Day 3 user attempt Phase 3 exercises or drown in 15 metrics

---

## MVP Roadmap

### MVP 1 (Current Scope)
- .webm audio upload from Android Recorder as primary input (with Whisper transcription)
- Paste transcript as fallback input
- Auto-extracted duration and WPM from audio
- Word-level timestamps for filler clustering analysis
- Phase-aware session setup with warm-up, topic, framework, and focus skills
- Full analysis pipeline: fillers, mazes, hedging, framework completion, 5-dimension scoring
- Phase-gated metrics (only show what's relevant)
- Feedback with scorecard + tips referencing specific techniques
- Local JSON storage with phase progression tracking
- Session history review + baseline comparison
- Baseline recording flow on first run

### MVP 2 (Future)
- Support for additional audio formats (mp3, wav, m4a)
- Whisper Flow / Granola transcript import (txt, md)
- Audio-level pause detection (duration, placement from Whisper timestamps) — unlocks true pause quality scoring
- Enhanced vocal delivery scoring from audio features (pitch, volume via librosa or similar)
- Exportable progress reports (markdown with trend charts)

### MVP 3 (Future)
- Real-time recording within the tool
- Claude-generated hostile Q&A questions (live in Phase 3)
- Side-by-side session comparison
- Custom topic/skill libraries
- Team/peer practice mode
- Integration with calendar for daily reminders
- 30/60/90-day milestone reports with full baseline comparison

---

## Success Metrics

- **Adoption:** User completes 5+ sessions per week for ≥4 consecutive weeks
- **Filler reduction:** ≥50% decline in filler rate by Day 30 (research-backed target)
- **Framework mastery:** >80% framework completion rate by end of Phase 1
- **Session duration:** User maintains ~10 min total workflow (warm-up → practice → review)
- **Phase progression:** User reaches Phase 2 within 30–40 days
- **Portability:** JSON file successfully used across 2+ devices

---

## Open Questions

1. **Whisper model size vs. filler fidelity:** Whisper comes in multiple sizes (tiny → large). Larger models are more accurate but slower. Need to test which model size reliably preserves fillers ("um," "uh") in transcription rather than silently dropping them. The `--word_timestamps` flag should help, but needs validation with actual Android Recorder .webm files. **Action:** Record a test .webm with deliberate fillers and test across Whisper model sizes.

2. **Whisper timestamp resolution for pause detection:** Whisper's word-level timestamps may enable rough pause detection (gaps >0.5s between words). If reliable, this unlocks pause quality scoring earlier than planned (potentially Phase 2 instead of MVP 2). **Action:** Test timestamp gap analysis on sample recordings.

3. **ffmpeg dependency for .webm:** Whisper may need .webm converted to wav/mp3 first via ffmpeg. Need to confirm the transcription pipeline: `.webm → ffmpeg → wav → Whisper → transcript + timestamps`. This adds a dependency but ffmpeg is widely available.

4. **Android Recorder .webm codec:** Android Recorder may use different audio codecs within .webm (Opus, Vorbis). Need to verify Whisper/ffmpeg handles the specific codec variant. **Action:** Check codec of test recording with `ffprobe`.

5. **Vocal delivery scoring:** The 15%-weighted "Vocal Delivery" dimension (pitch, volume, emphasis) cannot be reliably assessed from transcripts alone. With audio now available in MVP1, there's an option to use basic audio analysis (e.g., pitch variance via librosa). **Decision needed:** Include basic audio-derived vocal metrics in MVP1, or keep as user self-rating and defer deeper analysis to MVP2?

6. **Scoring calibration:** Initial rubric will need tuning. Plan for a calibration phase in first ~10 sessions where scores may be inconsistent. Consider a "calibration mode" flag in the JSON.

7. **Filler word disambiguation:** "So," "well," "like," "right," and "actually" can be fillers or meaningful words depending on context. The analysis prompt needs robust disambiguation guidance. Claude is well-suited to this but may need few-shot examples in the prompt.

8. **Overcorrection detection:** Research warns that zero fillers sounds robotic and reduces perceived authenticity. The tool should detect if filler rate drops to 0 for multiple sessions and flag potential overcorrection, suggesting the user maintain 1–2 strategic fillers per minute.

---

## Reference

This PRD is informed by the consolidated research document: *Speaking Clarity & Thought Clarity: Consolidated Reference* (synthesized from Perplexity Pro, Gemini, and Claude outputs, February 2026). Key sources include Levelt's speech production model (1989), Clark & Fox Tree's filler word research (2002), Ericsson's deliberate practice framework (1993), and scoring methodologies from Toastmasters, ETS SpeechRater, and NCA.
