# Whisper Model Filler Fidelity Testing Results

**Ticket:** 1.2.2 - Whisper filler fidelity testing
**Date:** 2026-02-16
**Purpose:** Determine which Whisper model size best preserves filler words for speaking analysis

## Executive Summary

This document reports the filler preservation rates for different Whisper model sizes when transcribing speech recordings containing deliberate filler words (um, uh, like, so, you know, etc.).

**Key Finding:** [To be determined after testing]

**Recommended Default Model:** [To be determined after testing]

---

## Testing Methodology

### Test Setup
- **Models Tested:** tiny, base, small, medium
- **Test Recordings:** Audio samples with known filler words
- **Ground Truth:** Manual transcripts with fillers marked
- **Evaluation Metric:** Filler preservation rate (% of ground truth fillers detected)

### Filler Lexicon
The following filler words were tracked:
- Single-word fillers: um, uh, ah, er, hmm
- Verbal crutches: like, so, actually, basically, literally, you know, I mean, kind of, sort of
- False starts: repeated words (the the, I I, we we)

### Test Command
```bash
python tests/filler_fidelity_test.py tests/fixtures/filler_samples/
```

---

## Results

### Model Comparison

| Model  | Avg Preservation Rate | Avg Detected Fillers | False Positives | Memory | Speed |
|--------|----------------------|---------------------|----------------|--------|-------|
| tiny   | TBD%                | TBD                 | TBD            | ~75MB  | Fast  |
| base   | TBD%                | TBD                 | TBD            | ~150MB | Fast  |
| small  | TBD%                | TBD                 | TBD            | ~500MB | Medium|
| medium | TBD%                | TBD                 | TBD            | ~1.5GB | Slow  |

### Detailed Results by Sample

#### Sample 1: Casual Meeting (15 fillers)
| Model  | Detected | Preserved | Missed | False Positives |
|--------|----------|-----------|--------|----------------|
| tiny   | TBD      | TBD       | TBD    | TBD            |
| base   | TBD      | TBD       | TBD    | TBD            |
| small  | TBD      | TBD       | TBD    | TBD            |
| medium | TBD      | TBD       | TBD    | TBD            |

#### Sample 2: Nervous Presentation (22 fillers)
| Model  | Detected | Preserved | Missed | False Positives |
|--------|----------|-----------|--------|----------------|
| tiny   | TBD      | TBD       | TBD    | TBD            |
| base   | TBD      | TBD       | TBD    | TBD            |
| small  | TBD      | TBD       | TBD    | TBD            |
| medium | TBD      | TBD       | TBD    | TBD            |

---

## Analysis

### Filler Types Most Affected
[To be completed after testing]

**Most Reliably Preserved:**
- TBD

**Most Frequently Missed:**
- TBD

**Most False Positives:**
- TBD

### Trade-offs

#### Tiny Model
**Pros:**
- Fast transcription (~2-3x real-time)
- Small memory footprint (~75MB)
- Good for low-resource environments

**Cons:**
- [TBD based on results]

#### Base Model
**Pros:**
- Balanced speed and accuracy
- Reasonable memory (~150MB)
- Default for most use cases

**Cons:**
- [TBD based on results]

#### Small Model
**Pros:**
- Better accuracy than tiny/base
- Still relatively fast
- Good compromise

**Cons:**
- Higher memory usage (~500MB)
- Slower than base

#### Medium Model
**Pros:**
- Best transcription accuracy
- Most reliable filler preservation

**Cons:**
- Large memory footprint (~1.5GB)
- Slowest transcription (~1x real-time)
- Overkill for most users

---

## Recommendations

### Default Model Selection
**Recommendation:** [TBD after testing]

**Rationale:** [TBD after testing]

### User Guidance
- **For most users:** Use `base` model (default)
- **For accuracy-critical analysis:** Use `small` or `medium`
- **For quick feedback/low resources:** Use `tiny` with caveat about potential filler under-detection

### Configuration
Users can override the model in `~/.clarity/config.json`:
```json
{
  "whisper_model": "base"
}
```

---

## Limitations

1. **Test Sample Size:** Results based on [N] audio samples
2. **Language:** Testing focused on English only
3. **Accents:** Limited accent diversity in test samples
4. **Context:** Results may vary with different speaking styles and audio quality

---

## Future Work

1. Test with larger sample set (50+ recordings)
2. Test with diverse accents and dialects
3. Evaluate performance on poor audio quality
4. Test multi-word filler phrases (e.g., "you know", "I mean")
5. Benchmark against other transcription services

---

## Appendix: Running Your Own Tests

### Creating Test Samples
1. Record audio with deliberate fillers
2. Save as `.webm` or `.wav`
3. Create matching `.txt` with ground truth transcript
4. Optionally create `.json` with metadata:
```json
{
  "expected_fillers": ["um", "uh", "like", "so"],
  "filler_count": 4,
  "speaker_metadata": {
    "accent": "American",
    "speaking_rate": "medium"
  }
}
```

### Run Tests
```bash
python tests/filler_fidelity_test.py path/to/samples/ --output results.json
```

### Analyze Results
Results are saved to `docs/whisper_fidelity_results.json` with detailed per-model, per-sample data.

---

**Last Updated:** 2026-02-16
**Next Review:** After collecting more test samples
