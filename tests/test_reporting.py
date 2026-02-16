"""Tests for the reporting modules."""

import pytest

from clarity.reporting.csv_logger import CSVLogger
from clarity.reporting.plotter import MetricsPlotter
from clarity.reporting.report_generator import ReportGenerator


@pytest.fixture
def sample_results():
    """Sample analysis results for testing."""
    return {
        "transcript": "Hello this is a test",
        "speaking_rate": {"word_count": 5, "wpm": 150.0, "duration_seconds": 2.0},
        "fillers": {"total_filler_count": 2, "filler_breakdown": {"um": 1, "uh": 1}},
        "pauses": {
            "pause_count": 3,
            "total_pause_duration": 1.5,
            "avg_pause_duration": 0.5,
            "pause_percentage": 25.0,
        },
        "energy": {
            "mean_energy_db": -50.0,
            "std_energy_db": 10.0,
            "max_energy_db": -30.0,
            "min_energy_db": -70.0,
        },
        "pitch": {
            "mean_pitch_hz": 200.0,
            "std_pitch_hz": 20.0,
            "min_pitch_hz": 150.0,
            "max_pitch_hz": 250.0,
            "pitch_range_hz": 100.0,
        },
    }


def test_csv_logger_log(sample_results, tmp_path):
    """Test logging to CSV."""
    csv_path = tmp_path / "test_log.csv"
    logger = CSVLogger(csv_path)

    # Log a session
    logger.log("test.webm", sample_results)

    # Verify file was created and has content
    assert csv_path.exists()
    content = csv_path.read_text()
    assert "timestamp" in content
    assert "test.webm" in content
    assert "150.0" in content  # WPM


def test_csv_logger_read_all(sample_results, tmp_path):
    """Test reading from CSV."""
    csv_path = tmp_path / "test_log.csv"
    logger = CSVLogger(csv_path)

    # Log multiple sessions
    logger.log("test1.webm", sample_results)
    logger.log("test2.webm", sample_results)

    # Read back
    sessions = logger.read_all()

    assert len(sessions) == 2
    assert sessions[0]["filename"] == "test1.webm"
    assert sessions[1]["filename"] == "test2.webm"
    assert float(sessions[0]["wpm"]) == 150.0


def test_csv_logger_read_empty(tmp_path):
    """Test reading from nonexistent CSV."""
    csv_path = tmp_path / "nonexistent.csv"
    logger = CSVLogger(csv_path)

    sessions = logger.read_all()
    assert sessions == []


def test_report_generator(tmp_path):
    """Test markdown report generation."""
    report_path = tmp_path / "test_report.md"

    # Create sample sessions
    sessions = [
        {
            "timestamp": "2026-01-01T10:00:00",
            "filename": "test1.webm",
            "duration_seconds": "2.0",
            "word_count": "5",
            "wpm": "150.0",
            "filler_count": "2",
            "pause_count": "3",
            "pause_percentage": "25.0",
            "mean_energy_db": "-50.0",
            "mean_pitch_hz": "200.0",
        },
        {
            "timestamp": "2026-01-02T10:00:00",
            "filename": "test2.webm",
            "duration_seconds": "3.0",
            "word_count": "8",
            "wpm": "160.0",
            "filler_count": "1",
            "pause_count": "2",
            "pause_percentage": "20.0",
            "mean_energy_db": "-45.0",
            "mean_pitch_hz": "210.0",
        },
    ]

    # Generate report
    report_gen = ReportGenerator()
    report_gen.generate(sessions, report_path)

    # Verify report was created
    assert report_path.exists()
    content = report_path.read_text()

    # Check key sections
    assert "Speaking Clarity Practice Report" in content
    assert "Total Sessions: 2" in content
    assert "Summary Statistics" in content
    assert "Recent Sessions" in content
    assert "Progress Notes" in content


def test_metrics_plotter(tmp_path):
    """Test plotting metrics."""
    plot_path = tmp_path / "test_plot.png"

    # Create sample sessions
    sessions = [
        {
            "timestamp": "2026-01-01T10:00:00",
            "wpm": "150.0",
            "filler_count": "2",
            "pause_count": "3",
            "pause_percentage": "25.0",
            "mean_energy_db": "-50.0",
            "mean_pitch_hz": "200.0",
        },
        {
            "timestamp": "2026-01-02T10:00:00",
            "wpm": "160.0",
            "filler_count": "1",
            "pause_count": "2",
            "pause_percentage": "20.0",
            "mean_energy_db": "-45.0",
            "mean_pitch_hz": "210.0",
        },
    ]

    # Generate plot
    plotter = MetricsPlotter()
    plotter.plot_metrics(sessions, plot_path)

    # Verify plot was created
    assert plot_path.exists()
    assert plot_path.stat().st_size > 0  # File has content
