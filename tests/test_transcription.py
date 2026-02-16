"""
Tests for transcription module.

Tests word-level timestamps, metrics calculation, and filler detection.
"""

import pytest

from clarity.transcription import (
    SpeakingMetrics,
    TranscriptionResult,
    WordTimestamp,
    calculate_metrics,
    detect_fillers,
)


@pytest.fixture
def sample_words():
    """Create sample word timestamps for testing."""
    return [
        WordTimestamp("Hello", 0.0, 0.5),
        WordTimestamp("um", 0.5, 0.8),
        WordTimestamp("this", 1.0, 1.3),
        WordTimestamp("is", 1.3, 1.5),
        WordTimestamp("a", 1.5, 1.6),
        WordTimestamp("like", 1.6, 1.9),  # Filler
        WordTimestamp("test", 2.0, 2.4),
        WordTimestamp("of", 2.4, 2.6),
        WordTimestamp("the", 2.6, 2.8),
        WordTimestamp("uh", 3.0, 3.2),  # Filler
        WordTimestamp("system", 3.4, 3.9),
    ]


@pytest.fixture
def sample_transcription(sample_words):
    """Create sample transcription result."""
    transcript = " ".join([w.word for w in sample_words])
    return TranscriptionResult(
        transcript=transcript,
        words=sample_words,
        duration_seconds=3.9,
        word_count=len(sample_words),
        language="en",
        model_used="base",
    )


def test_transcription_result_structure(sample_transcription):
    """Test TranscriptionResult dataclass structure."""
    assert sample_transcription.transcript is not None
    assert len(sample_transcription.words) > 0
    assert sample_transcription.duration_seconds > 0
    assert sample_transcription.word_count == len(sample_transcription.words)
    assert sample_transcription.language == "en"
    assert sample_transcription.model_used == "base"


def test_word_timestamp_structure():
    """Test WordTimestamp dataclass structure."""
    word = WordTimestamp("hello", 0.0, 0.5)
    assert word.word == "hello"
    assert word.start == 0.0
    assert word.end == 0.5


def test_calculate_metrics_basic(sample_transcription):
    """Test basic metrics calculation."""
    metrics = calculate_metrics(sample_transcription)

    assert isinstance(metrics, SpeakingMetrics)
    assert metrics.duration_seconds == 3.9
    assert metrics.word_count == 11
    assert metrics.wpm > 0


def test_calculate_wpm(sample_transcription):
    """Test WPM calculation."""
    metrics = calculate_metrics(sample_transcription)

    # 11 words in 3.9 seconds = ~169 WPM
    expected_wpm = (11 / 3.9) * 60
    assert abs(metrics.wpm - expected_wpm) < 0.1


def test_detect_fillers_count(sample_words):
    """Test filler detection count."""
    filler_words, positions = detect_fillers(sample_words, 3.9)

    # Should detect: um, like, uh
    assert len(filler_words) == 3
    assert len(positions) == 3


def test_detect_fillers_identification(sample_words):
    """Test that correct words are identified as fillers."""
    filler_words, _ = detect_fillers(sample_words, 3.9)

    filler_texts = [w.word.lower() for w in filler_words]
    assert "um" in filler_texts
    assert "like" in filler_texts
    assert "uh" in filler_texts


def test_filler_positions(sample_words):
    """Test filler position categorization."""
    filler_words, positions = detect_fillers(sample_words, 3.9)

    # All positions should be valid categories
    valid_positions = {"opening", "middle", "closing", "transition"}
    assert all(pos in valid_positions for pos in positions)


def test_filler_opening_position():
    """Test detection of fillers in opening segment."""
    words = [
        WordTimestamp("um", 0.1, 0.3),  # In first 20%
        WordTimestamp("hello", 0.5, 1.0),
        WordTimestamp("world", 1.0, 1.5),
    ]

    _, positions = detect_fillers(words, 5.0)
    assert positions[0] == "opening"


def test_filler_closing_position():
    """Test detection of fillers in closing segment."""
    words = [
        WordTimestamp("hello", 0.0, 0.5),
        WordTimestamp("world", 0.5, 1.0),
        WordTimestamp("this", 1.0, 1.3),
        WordTimestamp("is", 1.3, 1.5),
        WordTimestamp("test", 1.5, 2.0),
        WordTimestamp("speech", 4.0, 4.4),  # Keep gap < 0.5s
        WordTimestamp("um", 4.5, 4.8),  # In last 20% of 5s
    ]

    _, positions = detect_fillers(words, 5.0)
    assert positions[0] == "closing"


def test_filler_transition_position():
    """Test detection of fillers at transitions (after pauses)."""
    words = [
        WordTimestamp("hello", 0.0, 0.5),
        # Long pause here (1.5s)
        WordTimestamp("um", 2.0, 2.2),  # After pause
        WordTimestamp("world", 2.5, 3.0),
    ]

    _, positions = detect_fillers(words, 5.0)
    assert positions[0] == "transition"


def test_calculate_metrics_with_fillers(sample_transcription):
    """Test metrics calculation includes filler statistics."""
    metrics = calculate_metrics(sample_transcription)

    assert metrics.filler_count == 3
    assert metrics.filler_rate > 0
    assert len(metrics.filler_positions) == 3


def test_filler_rate_calculation():
    """Test filler rate (fillers per minute) calculation."""
    words = [
        WordTimestamp("um", 0.0, 0.2),
        WordTimestamp("test", 0.5, 1.0),
        WordTimestamp("uh", 1.5, 1.7),
    ]

    result = TranscriptionResult(
        transcript="um test uh",
        words=words,
        duration_seconds=1.7,
        word_count=3,
        language="en",
        model_used="base",
    )

    metrics = calculate_metrics(result)

    # 2 fillers in 1.7 seconds
    expected_rate = (2 / 1.7) * 60  # ~70.6 fillers per minute
    assert abs(metrics.filler_rate - expected_rate) < 0.1


def test_zero_duration_handling():
    """Test metrics calculation handles zero duration gracefully."""
    words = [WordTimestamp("test", 0.0, 0.0)]

    result = TranscriptionResult(
        transcript="test",
        words=words,
        duration_seconds=0.0,
        word_count=1,
        language="en",
        model_used="base",
    )

    metrics = calculate_metrics(result)

    assert metrics.wpm == 0.0
    assert metrics.filler_rate == 0.0


def test_no_fillers():
    """Test metrics when no fillers are present."""
    words = [
        WordTimestamp("hello", 0.0, 0.5),
        WordTimestamp("world", 0.5, 1.0),
        WordTimestamp("test", 1.0, 1.5),
    ]

    result = TranscriptionResult(
        transcript="hello world test",
        words=words,
        duration_seconds=1.5,
        word_count=3,
        language="en",
        model_used="base",
    )

    metrics = calculate_metrics(result)

    assert metrics.filler_count == 0
    assert metrics.filler_rate == 0.0
    assert len(metrics.filler_positions) == 0


def test_empty_words_list():
    """Test metrics calculation with empty words list."""
    result = TranscriptionResult(
        transcript="",
        words=[],
        duration_seconds=0.0,
        word_count=0,
        language="en",
        model_used="base",
    )

    metrics = calculate_metrics(result)

    assert metrics.word_count == 0
    assert metrics.wpm == 0.0
    assert metrics.filler_count == 0


def test_case_insensitive_filler_detection():
    """Test that filler detection is case-insensitive."""
    words = [
        WordTimestamp("Um", 0.0, 0.2),  # Capital U
        WordTimestamp("test", 0.5, 1.0),
        WordTimestamp("UH", 1.5, 1.7),  # All caps
    ]

    filler_words, _ = detect_fillers(words, 2.0)

    assert len(filler_words) == 2
    filler_texts = [w.word.lower() for w in filler_words]
    assert "um" in filler_texts
    assert "uh" in filler_texts


def test_multiword_filler_lexicon():
    """Test that FILLER_LEXICON includes multi-word phrases."""
    from clarity.transcription.metrics import FILLER_LEXICON

    assert "you know" in FILLER_LEXICON
    assert "i mean" in FILLER_LEXICON
    assert "kind of" in FILLER_LEXICON


def test_common_fillers_in_lexicon():
    """Test that common fillers are in the lexicon."""
    from clarity.transcription.metrics import FILLER_LEXICON

    common_fillers = ["um", "uh", "like", "so", "actually", "basically"]
    for filler in common_fillers:
        assert filler in FILLER_LEXICON


def test_metrics_with_realistic_speech():
    """Test metrics with realistic speaking pattern."""
    # Simulate 30 seconds of speech at ~150 WPM
    words = []
    current_time = 0.0

    speech_words = [
        "Hello",
        "everyone",
        "um",  # Filler
        "today",
        "I",
        "want",
        "to",
        "like",  # Filler
        "talk",
        "about",
        "the",
        "project",
        "we",
        "are",
        "working",
        "on",
        "uh",  # Filler
        "it",
        "has",
        "been",
        "really",
        "interesting",
    ]

    for word in speech_words:
        duration = 0.3 if len(word) > 5 else 0.2
        words.append(WordTimestamp(word, current_time, current_time + duration))
        current_time += duration + 0.1  # Small gap between words

    result = TranscriptionResult(
        transcript=" ".join(speech_words),
        words=words,
        duration_seconds=current_time,
        word_count=len(speech_words),
        language="en",
        model_used="base",
    )

    metrics = calculate_metrics(result)

    # Validate realistic values
    assert metrics.word_count == len(speech_words)
    assert 100 < metrics.wpm < 250  # Typical speaking rate
    assert metrics.filler_count == 3  # um, like, uh
    assert metrics.filler_rate > 0
