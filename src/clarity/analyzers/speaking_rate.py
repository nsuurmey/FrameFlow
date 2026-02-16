"""
Speaking rate (words per minute) calculator.

Calculates WPM based on word count and audio duration.
"""


class SpeakingRateCalculator:
    """
    Calculates speaking rate in words per minute (WPM).

    Uses word count from transcription and audio duration.
    """

    def analyze(self, transcript: str, duration_seconds: float) -> dict[str, float]:
        """
        Calculate speaking rate.

        Args:
            transcript: Transcribed text
            duration_seconds: Duration of audio in seconds

        Returns:
            Dictionary with speaking rate metrics:
                - word_count: Total number of words
                - wpm: Words per minute
                - duration_seconds: Duration of audio
        """
        # Count words by splitting on whitespace
        words = transcript.split()
        word_count = len(words)

        # Calculate WPM
        duration_minutes = duration_seconds / 60.0
        wpm = word_count / duration_minutes if duration_minutes > 0 else 0.0

        return {
            "word_count": word_count,
            "wpm": wpm,
            "duration_seconds": duration_seconds,
        }
