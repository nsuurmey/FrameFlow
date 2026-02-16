"""
Calculate speaking metrics from transcription timestamps.

Computes duration, WPM, and filler positions from Whisper output.
"""

from dataclasses import dataclass

from clarity.transcription.whisper_service import TranscriptionResult, WordTimestamp


@dataclass
class SpeakingMetrics:
    """Computed speaking metrics from transcription."""

    duration_seconds: float
    word_count: int
    wpm: float  # Words per minute
    filler_count: int
    filler_rate: float  # Fillers per minute
    filler_positions: list[str]  # opening, middle, closing, transition


# Common filler words and phrases
FILLER_LEXICON = {
    # Single-word fillers
    "um",
    "uh",
    "ah",
    "er",
    "eh",
    "hmm",
    "hm",
    "mm",
    # Common verbal crutches
    "like",
    "you know",
    "so",
    "actually",
    "basically",
    "literally",
    "right",
    "okay",
    "well",
    "i mean",
    "kind of",
    "sort of",
    # False starts (often part of mazes)
    "i i",
    "the the",
    "we we",
}


def calculate_metrics(result: TranscriptionResult) -> SpeakingMetrics:
    """
    Calculate speaking metrics from transcription result.

    Args:
        result: TranscriptionResult with word-level timestamps

    Returns:
        SpeakingMetrics with calculated values
    """
    duration = result.duration_seconds
    word_count = result.word_count

    # Calculate WPM
    if duration > 0:
        wpm = (word_count / duration) * 60
    else:
        wpm = 0.0

    # Detect fillers
    filler_words, filler_positions = detect_fillers(
        result.words, duration
    )
    filler_count = len(filler_words)

    # Calculate filler rate
    if duration > 0:
        filler_rate = (filler_count / duration) * 60
    else:
        filler_rate = 0.0

    return SpeakingMetrics(
        duration_seconds=duration,
        word_count=word_count,
        wpm=wpm,
        filler_count=filler_count,
        filler_rate=filler_rate,
        filler_positions=filler_positions,
    )


def detect_fillers(
    words: list[WordTimestamp], total_duration: float
) -> tuple[list[WordTimestamp], list[str]]:
    """
    Detect filler words and their positions in speech.

    Positions are mapped to speech segments:
    - opening: first 20% of speech
    - closing: last 20% of speech
    - middle: middle 60% of speech
    - transition: between sentences/thoughts

    Args:
        words: List of word timestamps
        total_duration: Total speech duration in seconds

    Returns:
        Tuple of (filler_words, position_labels)
    """
    filler_words = []
    positions = []

    # Define segment boundaries
    opening_threshold = total_duration * 0.2
    closing_threshold = total_duration * 0.8

    for i, word in enumerate(words):
        word_lower = word.word.lower().strip()

        # Check if word is a filler
        if word_lower in FILLER_LEXICON:
            filler_words.append(word)

            # Determine position
            if word.start < opening_threshold:
                position = "opening"
            elif word.start > closing_threshold:
                position = "closing"
            else:
                position = "middle"

            # Check if it's at a transition point
            # (after a pause > 0.5s or at sentence boundary)
            if i > 0:
                prev_word = words[i - 1]
                gap = word.start - prev_word.end
                if gap > 0.5:  # Pause longer than 0.5s
                    position = "transition"

            positions.append(position)

    return filler_words, positions


def calculate_wpm_by_segment(
    words: list[WordTimestamp], segment_duration: float = 30.0
) -> list[float]:
    """
    Calculate WPM for time segments of speech.

    Useful for detecting pacing variations.

    Args:
        words: List of word timestamps
        segment_duration: Duration of each segment in seconds

    Returns:
        List of WPM values for each segment
    """
    if not words:
        return []

    total_duration = words[-1].end
    num_segments = int(total_duration / segment_duration) + 1

    segment_wpms = []

    for segment_idx in range(num_segments):
        segment_start = segment_idx * segment_duration
        segment_end = segment_start + segment_duration

        # Count words in this segment
        segment_words = [
            w
            for w in words
            if segment_start <= w.start < segment_end
        ]

        if segment_words:
            # Calculate WPM for this segment
            actual_duration = segment_words[-1].end - segment_words[0].start
            if actual_duration > 0:
                wpm = (len(segment_words) / actual_duration) * 60
                segment_wpms.append(wpm)
            else:
                segment_wpms.append(0.0)
        else:
            segment_wpms.append(0.0)

    return segment_wpms


def find_longest_pause(words: list[WordTimestamp]) -> tuple[float, float]:
    """
    Find the longest pause between words.

    Args:
        words: List of word timestamps

    Returns:
        Tuple of (pause_duration, pause_start_time)
    """
    if len(words) < 2:
        return (0.0, 0.0)

    max_pause = 0.0
    max_pause_start = 0.0

    for i in range(1, len(words)):
        pause = words[i].start - words[i - 1].end
        if pause > max_pause:
            max_pause = pause
            max_pause_start = words[i - 1].end

    return (max_pause, max_pause_start)


def get_words_in_timerange(
    words: list[WordTimestamp], start: float, end: float
) -> list[WordTimestamp]:
    """
    Extract words within a specific time range.

    Args:
        words: List of word timestamps
        start: Start time in seconds
        end: End time in seconds

    Returns:
        List of words within the range
    """
    return [w for w in words if start <= w.start <= end]
