"""
Markdown report generation.

Creates formatted markdown reports with metrics tables and plots.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd


class ReportGenerator:
    """
    Generates markdown reports from analysis sessions.

    Creates a summary report with statistics and trends.
    """

    def generate(
        self,
        sessions: list[dict],
        output_path: str | Path = "clarity_report.md",
        plot_path: str | Path | None = None,
    ) -> None:
        """
        Generate a markdown report from logged sessions.

        Args:
            sessions: List of session dictionaries from CSVLogger
            output_path: Path to save the markdown report
            plot_path: Optional path to metrics plot to embed
        """
        if not sessions:
            print("No sessions to report")
            return

        # Convert to DataFrame for stats
        df = pd.DataFrame(sessions)
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

        # Build markdown report
        lines = []

        # Header
        lines.append("# Speaking Clarity Practice Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\nTotal Sessions: {len(sessions)}")
        lines.append("")

        # Summary Statistics
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append("| Metric | Mean | Std Dev | Min | Max |")
        lines.append("|--------|------|---------|-----|-----|")

        metrics = [
            ("Speaking Rate (WPM)", "wpm", 1),
            ("Filler Words", "filler_count", 1),
            ("Pause Count", "pause_count", 1),
            ("Pause %", "pause_percentage", 1),
            ("Energy (dB)", "mean_energy_db", 1),
            ("Pitch (Hz)", "mean_pitch_hz", 1),
        ]

        for label, col, decimals in metrics:
            mean_val = df[col].mean()
            std_val = df[col].std()
            min_val = df[col].min()
            max_val = df[col].max()

            lines.append(
                f"| {label} | {mean_val:.{decimals}f} | {std_val:.{decimals}f} | "
                f"{min_val:.{decimals}f} | {max_val:.{decimals}f} |"
            )

        lines.append("")

        # Recent Sessions Table
        lines.append("## Recent Sessions (Last 10)")
        lines.append("")
        lines.append("| Date | File | WPM | Fillers | Pauses | Pause % |")
        lines.append("|------|------|-----|---------|--------|---------|")

        # Show last 10 sessions
        recent = sessions[-10:]
        for session in reversed(recent):  # Most recent first
            timestamp = datetime.fromisoformat(session["timestamp"])
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            filename = Path(session["filename"]).name

            lines.append(
                f"| {date_str} | {filename} | {float(session['wpm']):.1f} | "
                f"{session['filler_count']} | {session['pause_count']} | "
                f"{float(session['pause_percentage']):.1f}% |"
            )

        lines.append("")

        # Embed plot if provided
        if plot_path:
            plot_path = Path(plot_path)
            if plot_path.exists():
                lines.append("## Metrics Over Time")
                lines.append("")
                lines.append(f"![Metrics Plot]({plot_path.name})")
                lines.append("")

        # Progress Notes
        lines.append("## Progress Notes")
        lines.append("")

        if len(sessions) >= 2:
            # Compare first and last session
            first = {k: float(v) if k in numeric_cols else v for k, v in sessions[0].items()}
            last = {k: float(v) if k in numeric_cols else v for k, v in sessions[-1].items()}

            improvements = []
            regressions = []

            # WPM: higher is better
            wpm_change = last["wpm"] - first["wpm"]
            if wpm_change > 0:
                improvements.append(f"Speaking rate improved by {wpm_change:.1f} WPM")
            elif wpm_change < 0:
                regressions.append(f"Speaking rate decreased by {abs(wpm_change):.1f} WPM")

            # Fillers: lower is better
            filler_change = last["filler_count"] - first["filler_count"]
            if filler_change < 0:
                improvements.append(
                    f"Filler words reduced by {abs(int(filler_change))} per session"
                )
            elif filler_change > 0:
                regressions.append(f"Filler words increased by {int(filler_change)} per session")

            # Pause percentage: lower is generally better
            pause_change = last["pause_percentage"] - first["pause_percentage"]
            if pause_change < 0:
                improvements.append(f"Pause percentage reduced by {abs(pause_change):.1f}%")
            elif pause_change > 5:  # Only report if significant
                regressions.append(f"Pause percentage increased by {pause_change:.1f}%")

            if improvements:
                lines.append("**Improvements:**")
                for imp in improvements:
                    lines.append(f"- ✓ {imp}")
                lines.append("")

            if regressions:
                lines.append("**Areas to Focus On:**")
                for reg in regressions:
                    lines.append(f"- ⚠ {reg}")
                lines.append("")

        # Write report
        report_text = "\n".join(lines)
        Path(output_path).write_text(report_text)

        print(f"✓ Report saved to: {output_path}")
