"""
Filler word detection.

Detects filler words like "um", "uh", "like" in transcribed speech.
"""

import re


class FillerDetector:
    """
    Detects filler words in transcribed text.

    Identifies common filler words that reduce speaking clarity.
    """

    # Default filler words to detect
    DEFAULT_FILLERS = {
        "um",
        "uh",
        "er",
        "ah",
        "like",
        "you know",
        "so",
        "actually",
        "basically",
        "literally",
    }

    def __init__(self, filler_words: set[str] | None = None) -> None:
        """
        Initialize the FillerDetector.

        Args:
            filler_words: Set of filler words to detect (default: common English fillers)
        """
        self.filler_words = filler_words if filler_words is not None else self.DEFAULT_FILLERS

    def analyze(self, transcript: str) -> dict[str, int | dict[str, int]]:
        """
        Analyze transcript for filler words.

        Args:
            transcript: Transcribed text

        Returns:
            Dictionary with filler metrics:
                - total_filler_count: Total number of filler words detected
                - filler_breakdown: Dictionary mapping each filler word to its count
        """
        # Normalize transcript to lowercase
        text_lower = transcript.lower()

        filler_breakdown = {}
        total_count = 0

        # Count each filler word
        for filler in self.filler_words:
            # Use word boundaries to avoid partial matches
            # For multi-word fillers like "you know", match the full phrase
            if " " in filler:
                pattern = re.escape(filler)
            else:
                pattern = r"\b" + re.escape(filler) + r"\b"

            matches = re.findall(pattern, text_lower)
            count = len(matches)

            if count > 0:
                filler_breakdown[filler] = count
                total_count += count

        return {
            "total_filler_count": total_count,
            "filler_breakdown": filler_breakdown,
        }
