"""
Main analyzer that integrates all individual analyzers.

Coordinates running all analysis modules and collecting results.
"""

import numpy as np

from .energy_analyzer import EnergyAnalyzer
from .filler_detector import FillerDetector
from .pause_detector import PauseDetector
from .pitch_analyzer import PitchAnalyzer
from .speaking_rate import SpeakingRateCalculator
from .transcriber import Transcriber


class ClarityAnalyzer:
    """
    Main analyzer that runs all speech clarity metrics.

    Coordinates transcription, filler detection, pause detection,
    speaking rate, energy, and pitch analysis.
    """

    def __init__(self) -> None:
        """Initialize all sub-analyzers."""
        self.transcriber = Transcriber()
        self.filler_detector = FillerDetector()
        self.pause_detector = PauseDetector()
        self.speaking_rate_calculator = SpeakingRateCalculator()
        self.energy_analyzer = EnergyAnalyzer()
        self.pitch_analyzer = PitchAnalyzer()

    def analyze(self, audio: np.ndarray, sample_rate: int) -> dict:
        """
        Run all analyzers on audio and return comprehensive metrics.

        Args:
            audio: Audio samples as 1D numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Dictionary containing all metrics:
                - transcript: Full transcription
                - fillers: Filler word metrics
                - pauses: Pause detection metrics
                - speaking_rate: WPM and word count
                - energy: Energy/volume metrics
                - pitch: Pitch/F0 metrics
        """
        # Calculate audio duration
        duration_seconds = len(audio) / sample_rate

        # Step 1: Transcribe audio (needed for fillers and WPM)
        print("  [1/6] Transcribing audio...")
        transcript = self.transcriber.transcribe(audio, sample_rate)

        # Step 2: Detect filler words
        print("  [2/6] Detecting filler words...")
        filler_results = self.filler_detector.analyze(transcript)

        # Step 3: Detect pauses
        print("  [3/6] Detecting pauses...")
        pause_results = self.pause_detector.analyze(audio, sample_rate)

        # Step 4: Calculate speaking rate
        print("  [4/6] Calculating speaking rate...")
        speaking_rate_results = self.speaking_rate_calculator.analyze(
            transcript, duration_seconds
        )

        # Step 5: Analyze energy
        print("  [5/6] Analyzing energy...")
        energy_results = self.energy_analyzer.analyze(audio, sample_rate)

        # Step 6: Analyze pitch
        print("  [6/6] Analyzing pitch...")
        pitch_results = self.pitch_analyzer.analyze(audio, sample_rate)

        return {
            "transcript": transcript,
            "fillers": filler_results,
            "pauses": pause_results,
            "speaking_rate": speaking_rate_results,
            "energy": energy_results,
            "pitch": pitch_results,
        }
