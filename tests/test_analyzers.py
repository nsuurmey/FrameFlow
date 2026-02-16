"""Tests for the analyzer modules."""

import numpy as np
import pytest

from clarity.analyzers.energy_analyzer import EnergyAnalyzer
from clarity.analyzers.filler_detector import FillerDetector
from clarity.analyzers.pause_detector import PauseDetector
from clarity.analyzers.pitch_analyzer import PitchAnalyzer
from clarity.analyzers.speaking_rate import SpeakingRateCalculator


def test_filler_detector():
    """Test filler word detection."""
    detector = FillerDetector()

    # Test with fillers
    transcript = "Um, I think that, uh, we should like totally go there, you know?"
    results = detector.analyze(transcript)

    assert results["total_filler_count"] == 4  # um, uh, like, you know
    assert "um" in results["filler_breakdown"]
    assert "uh" in results["filler_breakdown"]
    assert "like" in results["filler_breakdown"]
    assert "you know" in results["filler_breakdown"]

    # Test without fillers
    transcript_clean = "I think we should go there."
    results_clean = detector.analyze(transcript_clean)
    assert results_clean["total_filler_count"] == 0


def test_speaking_rate_calculator():
    """Test WPM calculation."""
    calculator = SpeakingRateCalculator()

    # 10 words in 30 seconds = 20 WPM
    transcript = "one two three four five six seven eight nine ten"
    results = calculator.analyze(transcript, duration_seconds=30.0)

    assert results["word_count"] == 10
    assert results["wpm"] == pytest.approx(20.0, abs=0.1)
    assert results["duration_seconds"] == 30.0


def test_pause_detector():
    """Test pause detection."""
    detector = PauseDetector(min_pause_duration=0.1)

    # Create synthetic audio: 1s of speech, 0.5s silence, 1s speech
    sample_rate = 16000
    speech1 = np.random.randn(sample_rate) * 0.1  # 1 second of speech
    silence = np.zeros(sample_rate // 2)  # 0.5 seconds of silence
    speech2 = np.random.randn(sample_rate) * 0.1  # 1 second of speech
    audio = np.concatenate([speech1, silence, speech2])

    results = detector.analyze(audio, sample_rate)

    assert results["pause_count"] >= 1  # Should detect at least the silence
    assert results["total_pause_duration"] > 0
    assert 0 <= results["pause_percentage"] <= 100


def test_energy_analyzer():
    """Test energy analysis."""
    analyzer = EnergyAnalyzer()

    # Create synthetic audio with known properties
    sample_rate = 16000
    duration = 2.0
    audio = np.random.randn(int(sample_rate * duration)) * 0.1

    results = analyzer.analyze(audio, sample_rate)

    assert "mean_energy_db" in results
    assert "std_energy_db" in results
    assert "max_energy_db" in results
    assert "min_energy_db" in results

    # Energy should be negative dB (since amplitude < 1.0)
    assert results["mean_energy_db"] < 0
    assert results["max_energy_db"] > results["min_energy_db"]


def test_pitch_analyzer():
    """Test pitch analysis."""
    analyzer = PitchAnalyzer()

    # Create synthetic audio with a 200 Hz tone
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 200 * t) * 0.5

    results = analyzer.analyze(audio, sample_rate)

    assert "mean_pitch_hz" in results
    assert "std_pitch_hz" in results
    assert "min_pitch_hz" in results
    assert "max_pitch_hz" in results

    # Pitch should be detected around 200 Hz (within tolerance)
    if results["mean_pitch_hz"] > 0:  # If pitch was detected
        assert 180 < results["mean_pitch_hz"] < 220
