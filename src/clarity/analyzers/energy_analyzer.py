"""
Energy/volume analysis.

Analyzes the energy (volume/loudness) distribution of audio.
"""

import numpy as np


class EnergyAnalyzer:
    """
    Analyzes energy (RMS volume) of audio.

    Provides metrics about the overall energy level and variability of the audio.
    """

    def __init__(self, frame_length_ms: float = 20.0) -> None:
        """
        Initialize the EnergyAnalyzer.

        Args:
            frame_length_ms: Frame length for energy calculation in milliseconds
        """
        self.frame_length_ms = frame_length_ms

    def analyze(self, audio: np.ndarray, sample_rate: int) -> dict[str, float]:
        """
        Analyze audio energy.

        Args:
            audio: Audio samples as 1D numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary with energy metrics:
                - mean_energy_db: Mean RMS energy in dB
                - std_energy_db: Standard deviation of energy in dB
                - max_energy_db: Maximum energy in dB
                - min_energy_db: Minimum energy in dB
        """
        # Calculate frame length in samples
        frame_length = int(self.frame_length_ms * sample_rate / 1000)
        hop_length = frame_length // 2  # 50% overlap

        # Calculate RMS energy for each frame
        energies_db = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i : i + frame_length]
            rms = np.sqrt(np.mean(frame**2))
            # Convert to dB (with epsilon to avoid log(0))
            energy_db = 20 * np.log10(rms + 1e-10)
            energies_db.append(energy_db)

        energies_db = np.array(energies_db)

        return {
            "mean_energy_db": float(np.mean(energies_db)),
            "std_energy_db": float(np.std(energies_db)),
            "max_energy_db": float(np.max(energies_db)),
            "min_energy_db": float(np.min(energies_db)),
        }
