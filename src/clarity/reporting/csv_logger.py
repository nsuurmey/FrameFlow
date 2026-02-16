"""
CSV logging for practice session tracking.

Saves analysis results to a CSV file for historical tracking.
"""

import csv
from datetime import datetime
from pathlib import Path


class CSVLogger:
    """
    Logs analysis results to CSV for tracking over time.

    Each row represents one analysis session with all metrics.
    """

    def __init__(self, csv_path: str | Path = "clarity_log.csv") -> None:
        """
        Initialize the CSV logger.

        Args:
            csv_path: Path to the CSV log file (default: clarity_log.csv in current dir)
        """
        self.csv_path = Path(csv_path)

        # Define CSV columns
        self.columns = [
            "timestamp",
            "filename",
            "duration_seconds",
            "word_count",
            "wpm",
            "filler_count",
            "pause_count",
            "pause_percentage",
            "mean_energy_db",
            "mean_pitch_hz",
        ]

    def log(self, filename: str, results: dict) -> None:
        """
        Log analysis results to CSV.

        Args:
            filename: Name of the analyzed audio file
            results: Analysis results dictionary from ClarityAnalyzer
        """
        # Check if file exists to determine if we need to write header
        file_exists = self.csv_path.exists()

        # Extract metrics from results
        row = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "duration_seconds": results["speaking_rate"]["duration_seconds"],
            "word_count": results["speaking_rate"]["word_count"],
            "wpm": results["speaking_rate"]["wpm"],
            "filler_count": results["fillers"]["total_filler_count"],
            "pause_count": results["pauses"]["pause_count"],
            "pause_percentage": results["pauses"]["pause_percentage"],
            "mean_energy_db": results["energy"]["mean_energy_db"],
            "mean_pitch_hz": results["pitch"]["mean_pitch_hz"],
        }

        # Write to CSV
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)

            # Write header if file is new
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    def read_all(self) -> list[dict]:
        """
        Read all logged sessions from CSV.

        Returns:
            List of dictionaries, one per logged session
        """
        if not self.csv_path.exists():
            return []

        with open(self.csv_path, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
