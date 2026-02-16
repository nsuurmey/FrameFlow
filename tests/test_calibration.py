"""
Calibration tests for MVP 0.

Tests the full pipeline with the sample fixture to validate metric accuracy.
"""

from pathlib import Path

import pytest

from clarity.analyzers.analyzer import ClarityAnalyzer
from clarity.audio_loader import AudioLoader


@pytest.fixture
def sample_fixture_path():
    """Path to the sample audio fixture."""
    return Path(__file__).parent / "fixtures" / "sample.webm"


def test_end_to_end_analysis(sample_fixture_path):
    """Test complete analysis pipeline with sample fixture."""
    # Load audio
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    assert len(audio_data) > 0
    assert sample_rate == 16000

    # Run full analysis
    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    # Verify all expected keys are present
    assert "transcript" in results
    assert "fillers" in results
    assert "pauses" in results
    assert "speaking_rate" in results
    assert "energy" in results
    assert "pitch" in results


def test_speaking_rate_calibration(sample_fixture_path):
    """Validate speaking rate metrics are in reasonable range."""
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    sr = results["speaking_rate"]

    # Validate structure
    assert "word_count" in sr
    assert "wpm" in sr
    assert "duration_seconds" in sr

    # Validate values are non-negative
    assert sr["word_count"] >= 0
    assert sr["wpm"] >= 0
    assert sr["duration_seconds"] > 0

    # WPM should be reasonable (0-300 WPM is typical range, MVP 0 may be lower due to fallback)
    assert 0 <= sr["wpm"] <= 500


def test_filler_detection_calibration(sample_fixture_path):
    """Validate filler word detection."""
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    fillers = results["fillers"]

    # Validate structure
    assert "total_filler_count" in fillers
    assert "filler_breakdown" in fillers

    # Validate values
    assert fillers["total_filler_count"] >= 0
    assert isinstance(fillers["filler_breakdown"], dict)

    # If fillers detected, breakdown should match total
    if fillers["total_filler_count"] > 0:
        assert sum(fillers["filler_breakdown"].values()) == fillers["total_filler_count"]


def test_pause_detection_calibration(sample_fixture_path):
    """Validate pause detection metrics."""
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    pauses = results["pauses"]

    # Validate structure
    assert "pause_count" in pauses
    assert "total_pause_duration" in pauses
    assert "avg_pause_duration" in pauses
    assert "pause_percentage" in pauses

    # Validate values
    assert pauses["pause_count"] >= 0
    assert pauses["total_pause_duration"] >= 0
    assert pauses["avg_pause_duration"] >= 0
    assert 0 <= pauses["pause_percentage"] <= 100

    # If pauses detected, avg should be calculated correctly
    if pauses["pause_count"] > 0:
        expected_avg = pauses["total_pause_duration"] / pauses["pause_count"]
        assert abs(pauses["avg_pause_duration"] - expected_avg) < 0.01


def test_energy_metrics_calibration(sample_fixture_path):
    """Validate energy/volume metrics."""
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    energy = results["energy"]

    # Validate structure
    assert "mean_energy_db" in energy
    assert "std_energy_db" in energy
    assert "max_energy_db" in energy
    assert "min_energy_db" in energy

    # Validate relationships
    assert energy["max_energy_db"] >= energy["mean_energy_db"]
    assert energy["mean_energy_db"] >= energy["min_energy_db"]
    assert energy["std_energy_db"] >= 0

    # Energy in dB should be reasonable (typically -100 to 0 dB for normalized audio)
    assert -200 <= energy["mean_energy_db"] <= 0


def test_pitch_metrics_calibration(sample_fixture_path):
    """Validate pitch metrics."""
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)

    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)

    pitch = results["pitch"]

    # Validate structure
    assert "mean_pitch_hz" in pitch
    assert "std_pitch_hz" in pitch
    assert "min_pitch_hz" in pitch
    assert "max_pitch_hz" in pitch
    assert "pitch_range_hz" in pitch

    # If pitch detected, validate relationships and ranges
    if pitch["mean_pitch_hz"] > 0:
        assert pitch["max_pitch_hz"] >= pitch["mean_pitch_hz"]
        assert pitch["mean_pitch_hz"] >= pitch["min_pitch_hz"]
        assert pitch["std_pitch_hz"] >= 0

        # Human voice pitch range: ~80-400 Hz
        assert 50 <= pitch["mean_pitch_hz"] <= 500
        expected_range = pitch["max_pitch_hz"] - pitch["min_pitch_hz"]
        assert abs(pitch["pitch_range_hz"] - expected_range) < 0.01
