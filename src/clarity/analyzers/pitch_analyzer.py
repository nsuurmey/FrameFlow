"""
Pitch analysis using fundamental frequency (F0) extraction.

Analyzes the pitch characteristics of speech.
"""

import librosa
import numpy as np


class PitchAnalyzer:
    """
    Analyzes pitch (fundamental frequency) of audio.

    Uses librosa's piptrack to extract F0 and provide pitch statistics.
    """

    def __init__(self, fmin: float = 80.0, fmax: float = 400.0) -> None:
        """
        Initialize the PitchAnalyzer.

        Args:
            fmin: Minimum frequency (Hz) for pitch detection (default 80 Hz for male voice)
            fmax: Maximum frequency (Hz) for pitch detection (default 400 Hz for female voice)
        """
        self.fmin = fmin
        self.fmax = fmax

    def analyze(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """
        Analyze audio pitch.

        Args:
            audio: Audio samples as 1D numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with pitch metrics:
                - mean_pitch_hz: Mean pitch in Hz
                - std_pitch_hz: Standard deviation of pitch in Hz
                - min_pitch_hz: Minimum pitch in Hz
                - max_pitch_hz: Maximum pitch in Hz
                - pitch_range_hz: Range of pitch (max - min) in Hz
        """
        # Extract pitch using librosa's piptrack
        pitches, magnitudes = librosa.piptrack(
            y=audio, sr=sample_rate, fmin=self.fmin, fmax=self.fmax, threshold=0.1
        )

        # Get the pitch with the highest magnitude at each time frame
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            # Only include non-zero pitches (voiced segments)
            if pitch > 0:
                pitch_values.append(pitch)

        if len(pitch_values) == 0:
            # No voiced segments detected
            return {
                "mean_pitch_hz": 0.0,
                "std_pitch_hz": 0.0,
                "min_pitch_hz": 0.0,
                "max_pitch_hz": 0.0,
                "pitch_range_hz": 0.0,
            }

        pitch_values = np.array(pitch_values)

        return {
            "mean_pitch_hz": float(np.mean(pitch_values)),
            "std_pitch_hz": float(np.std(pitch_values)),
            "min_pitch_hz": float(np.min(pitch_values)),
            "max_pitch_hz": float(np.max(pitch_values)),
            "pitch_range_hz": float(np.max(pitch_values) - np.min(pitch_values)),
        }
