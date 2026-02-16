"""
Pause detection analyzer.

Detects silent pauses in audio using energy-based thresholding.
"""

import numpy as np


class PauseDetector:
    """
    Detects pauses (silent segments) in audio.

    Uses energy-based thresholding to identify segments where the speaker is not talking.
    """

    def __init__(
        self,
        min_pause_duration: float = 0.3,
        energy_threshold_db: float = -40.0,
        frame_length_ms: float = 20.0,
    ) -> None:
        """
        Initialize the PauseDetector.

        Args:
            min_pause_duration: Minimum duration (seconds) to count as a pause
            energy_threshold_db: Energy threshold in dB below which audio is considered silent
            frame_length_ms: Frame length for energy calculation in milliseconds
        """
        self.min_pause_duration = min_pause_duration
        self.energy_threshold_db = energy_threshold_db
        self.frame_length_ms = frame_length_ms

    def analyze(self, audio: np.ndarray, sample_rate: int) -> dict[str, float | int]:
        """
        Analyze audio for pauses.

        Args:
            audio: Audio samples as 1D numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with pause metrics:
                - pause_count: Number of pauses detected
                - total_pause_duration: Total duration of all pauses in seconds
                - avg_pause_duration: Average pause duration in seconds
                - pause_percentage: Percentage of audio that is pause
        """
        # Calculate frame length in samples
        frame_length = int(self.frame_length_ms * sample_rate / 1000)
        hop_length = frame_length // 2  # 50% overlap

        # Calculate energy for each frame
        energies = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i : i + frame_length]
            # RMS energy
            rms = np.sqrt(np.mean(frame**2))
            # Convert to dB (with small epsilon to avoid log(0))
            energy_db = 20 * np.log10(rms + 1e-10)
            energies.append(energy_db)

        energies = np.array(energies)

        # Identify frames below energy threshold (silent)
        is_silent = energies < self.energy_threshold_db

        # Find contiguous silent regions
        pauses = []
        in_pause = False
        pause_start = 0

        for i, silent in enumerate(is_silent):
            if silent and not in_pause:
                # Start of a new pause
                in_pause = True
                pause_start = i
            elif not silent and in_pause:
                # End of a pause
                in_pause = False
                pause_duration = (i - pause_start) * hop_length / sample_rate
                if pause_duration >= self.min_pause_duration:
                    pauses.append(pause_duration)

        # Handle case where audio ends during a pause
        if in_pause:
            pause_duration = (len(is_silent) - pause_start) * hop_length / sample_rate
            if pause_duration >= self.min_pause_duration:
                pauses.append(pause_duration)

        # Calculate metrics
        pause_count = len(pauses)
        total_pause_duration = sum(pauses)
        avg_pause_duration = total_pause_duration / pause_count if pause_count > 0 else 0.0
        audio_duration = len(audio) / sample_rate
        pause_percentage = (
            (total_pause_duration / audio_duration * 100) if audio_duration > 0 else 0.0
        )

        return {
            "pause_count": pause_count,
            "total_pause_duration": total_pause_duration,
            "avg_pause_duration": avg_pause_duration,
            "pause_percentage": pause_percentage,
        }
