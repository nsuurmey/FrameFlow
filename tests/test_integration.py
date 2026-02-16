"""
End-to-end integration tests for MVP 0.

Tests complete workflows from audio file to report generation.
"""

from pathlib import Path

import pytest

from clarity.analyzers.analyzer import ClarityAnalyzer
from clarity.audio_loader import AudioLoader
from clarity.reporting.csv_logger import CSVLogger
from clarity.reporting.plotter import MetricsPlotter
from clarity.reporting.report_generator import ReportGenerator


@pytest.fixture
def sample_fixture_path():
    """Path to the sample audio fixture."""
    return Path(__file__).parent / "fixtures" / "sample.webm"


def test_full_analyze_workflow(sample_fixture_path, tmp_path):
    """Test complete analyze workflow: load → analyze → log."""
    csv_path = tmp_path / "test_log.csv"

    # Step 1: Load audio
    loader = AudioLoader(sample_rate=16000)
    audio_data, sample_rate = loader.load(sample_fixture_path)
    assert len(audio_data) > 0

    # Step 2: Analyze
    analyzer = ClarityAnalyzer()
    results = analyzer.analyze(audio_data, sample_rate)
    assert "transcript" in results

    # Step 3: Log to CSV
    logger = CSVLogger(csv_path)
    logger.log(str(sample_fixture_path), results)

    # Verify CSV was created
    assert csv_path.exists()

    # Verify can read back
    sessions = logger.read_all()
    assert len(sessions) == 1
    assert sessions[0]["filename"] == str(sample_fixture_path)


def test_full_report_workflow(sample_fixture_path, tmp_path):
    """Test complete report workflow: analyze → log → report → plot."""
    csv_path = tmp_path / "test_log.csv"
    report_path = tmp_path / "test_report.md"
    plot_path = tmp_path / "test_plot.png"

    # Step 1-3: Analyze and log (multiple sessions for meaningful report)
    loader = AudioLoader(sample_rate=16000)
    analyzer = ClarityAnalyzer()
    logger = CSVLogger(csv_path)

    for i in range(3):
        audio_data, sample_rate = loader.load(sample_fixture_path)
        results = analyzer.analyze(audio_data, sample_rate)
        logger.log(f"session{i}.webm", results)

    # Step 4: Generate plot
    sessions = logger.read_all()
    assert len(sessions) == 3

    plotter = MetricsPlotter()
    plotter.plot_metrics(sessions, plot_path)
    assert plot_path.exists()

    # Step 5: Generate report
    report_gen = ReportGenerator()
    report_gen.generate(sessions, report_path, plot_path)
    assert report_path.exists()

    # Verify report content
    report_content = report_path.read_text()
    assert "Speaking Clarity Practice Report" in report_content
    assert "Total Sessions: 3" in report_content
    assert "Summary Statistics" in report_content


def test_multiple_analysis_sessions(sample_fixture_path, tmp_path):
    """Test analyzing the same file multiple times and tracking progress."""
    csv_path = tmp_path / "test_log.csv"
    logger = CSVLogger(csv_path)
    loader = AudioLoader(sample_rate=16000)
    analyzer = ClarityAnalyzer()

    # Analyze 5 times
    for i in range(5):
        audio_data, sample_rate = loader.load(sample_fixture_path)
        results = analyzer.analyze(audio_data, sample_rate)
        logger.log(f"practice_session_{i+1}.webm", results)

    # Verify all sessions logged
    sessions = logger.read_all()
    assert len(sessions) == 5

    # Verify each session has required fields
    for session in sessions:
        assert "timestamp" in session
        assert "filename" in session
        assert "wpm" in session
        assert float(session["wpm"]) >= 0


def test_error_handling_missing_file(tmp_path):
    """Test graceful error handling for missing audio file."""
    loader = AudioLoader()

    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "nonexistent.webm")


def test_csv_persistence(sample_fixture_path, tmp_path):
    """Test that CSV log persists across multiple runs."""
    csv_path = tmp_path / "test_log.csv"
    loader = AudioLoader(sample_rate=16000)
    analyzer = ClarityAnalyzer()

    # First run - add 2 sessions
    logger1 = CSVLogger(csv_path)
    for i in range(2):
        audio_data, sample_rate = loader.load(sample_fixture_path)
        results = analyzer.analyze(audio_data, sample_rate)
        logger1.log(f"session_{i}.webm", results)

    # Second run - add 2 more sessions
    logger2 = CSVLogger(csv_path)
    for i in range(2, 4):
        audio_data, sample_rate = loader.load(sample_fixture_path)
        results = analyzer.analyze(audio_data, sample_rate)
        logger2.log(f"session_{i}.webm", results)

    # Verify all 4 sessions are in the log
    sessions = logger2.read_all()
    assert len(sessions) == 4
