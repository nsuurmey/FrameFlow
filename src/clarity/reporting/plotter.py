"""
Time-series plotting for metrics visualization.

Creates matplotlib plots showing metric trends over time.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


class MetricsPlotter:
    """
    Creates time-series plots of speech metrics.

    Generates line plots showing how metrics change over practice sessions.
    """

    def plot_metrics(
        self, sessions: list[dict], output_path: str | Path = "metrics_plot.png"
    ) -> None:
        """
        Create a multi-panel plot of all metrics over time.

        Args:
            sessions: List of session dictionaries from CSVLogger
            output_path: Path to save the plot image
        """
        if not sessions:
            print("No sessions to plot")
            return

        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(sessions)

        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Convert numeric columns
        numeric_cols = [
            "wpm",
            "filler_count",
            "pause_count",
            "pause_percentage",
            "mean_energy_db",
            "mean_pitch_hz",
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        # Create figure with subplots
        fig, axes = plt.subplots(3, 2, figsize=(12, 10))
        fig.suptitle("Speaking Clarity Metrics Over Time", fontsize=16)

        # Plot 1: WPM
        ax = axes[0, 0]
        ax.plot(df["timestamp"], df["wpm"], marker="o", linewidth=2)
        ax.set_title("Speaking Rate (WPM)")
        ax.set_ylabel("Words/Minute")
        ax.grid(True, alpha=0.3)

        # Plot 2: Filler Count
        ax = axes[0, 1]
        ax.plot(df["timestamp"], df["filler_count"], marker="o", linewidth=2, color="red")
        ax.set_title("Filler Words")
        ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3)

        # Plot 3: Pause Count
        ax = axes[1, 0]
        ax.plot(df["timestamp"], df["pause_count"], marker="o", linewidth=2, color="orange")
        ax.set_title("Pause Count")
        ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3)

        # Plot 4: Pause Percentage
        ax = axes[1, 1]
        ax.plot(
            df["timestamp"], df["pause_percentage"], marker="o", linewidth=2, color="purple"
        )
        ax.set_title("Pause Percentage")
        ax.set_ylabel("% of Audio")
        ax.grid(True, alpha=0.3)

        # Plot 5: Energy
        ax = axes[2, 0]
        ax.plot(df["timestamp"], df["mean_energy_db"], marker="o", linewidth=2, color="green")
        ax.set_title("Mean Energy")
        ax.set_ylabel("dB")
        ax.grid(True, alpha=0.3)

        # Plot 6: Pitch
        ax = axes[2, 1]
        ax.plot(df["timestamp"], df["mean_pitch_hz"], marker="o", linewidth=2, color="blue")
        ax.set_title("Mean Pitch")
        ax.set_ylabel("Hz")
        ax.grid(True, alpha=0.3)

        # Format x-axis for all subplots
        for ax in axes.flat:
            ax.tick_params(axis="x", rotation=45)
            # Format dates nicely
            if len(df) > 1:
                ax.set_xlabel("Date")

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"✓ Plot saved to: {output_path}")
