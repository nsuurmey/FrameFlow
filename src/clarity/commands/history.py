"""
History command - view past sessions (Ticket 1.6.3).

Shows session history with dates, topics, scores, trends.
"""

from datetime import datetime

from rich.console import Console
from rich.table import Table

from clarity.feedback import get_score_color
from clarity.storage import StorageManager


def run_history(limit: int = 10, show_all: bool = False) -> None:
    """
    Display practice session history.

    Args:
        limit: Number of sessions to show (default 10)
        show_all: Show all sessions (ignores limit)
    """
    console = Console()
    storage = StorageManager()

    # Read all sessions
    data = storage.read_all()
    sessions = data.get("sessions", [])

    if not sessions:
        console.print("\n[yellow]No sessions found. Run 'clarity practice' to start![/yellow]\n")
        return

    # Determine how many to show
    if show_all:
        sessions_to_show = sessions
    else:
        sessions_to_show = sessions[-limit:] if len(sessions) > limit else sessions

    # Reverse to show most recent first
    sessions_to_show = list(reversed(sessions_to_show))

    # Create table
    table = Table(title=f"📜 Session History ({len(sessions)} total)", show_header=True)

    table.add_column("#", justify="right", style="cyan", width=4)
    table.add_column("Date", style="white", width=12)
    table.add_column("Topic", width=35)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Phase", justify="center", width=8)
    table.add_column("WPM", justify="right", width=6)
    table.add_column("Trend", justify="center", width=6)

    # Track previous score for trend
    prev_score = None

    for i, session in enumerate(sessions_to_show):
        # Session number (1-indexed)
        session_num = len(sessions) - i

        # Date
        timestamp = session.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date_str = "Unknown"

        # Topic
        topic = session.get("topic", "Unknown")[:32]
        if len(session.get("topic", "")) > 32:
            topic += "..."

        # Score
        metrics = session.get("metrics", {})
        score = metrics.get("composite_score", 0)
        score_color = get_score_color(score)
        score_str = f"[{score_color}]{score}[/{score_color}]"

        # Phase
        phase_name = session.get("phase", "PHASE_1")
        phase_num = phase_name.split("_")[1] if "_" in phase_name else "1"

        # WPM
        wpm = metrics.get("speaking_rate_wpm", 0)
        wpm_str = f"{wpm:.0f}"

        # Trend (compare to previous session in reverse order)
        trend_str = ""
        if prev_score is not None:
            delta = score - prev_score
            if delta > 5:
                trend_str = "[green]↑[/green]"
            elif delta < -5:
                trend_str = "[red]↓[/red]"
            else:
                trend_str = "[dim]→[/dim]"

        table.add_row(
            str(session_num),
            date_str,
            topic,
            score_str,
            f"P{phase_num}",
            wpm_str,
            trend_str,
        )

        prev_score = score

    console.print()
    console.print(table)
    console.print()

    # Summary stats
    console.print("[bold cyan]Summary:[/bold cyan]")
    console.print(f"  • Total sessions: {len(sessions)}")

    # Calculate averages
    total_score = sum(s.get("metrics", {}).get("composite_score", 0) for s in sessions)
    avg_score = total_score / len(sessions) if sessions else 0

    console.print(f"  • Average score: {avg_score:.1f}")

    # Current phase
    if sessions:
        current_phase = sessions[-1].get("phase", "PHASE_1")
        phase_num = current_phase.split("_")[1] if "_" in current_phase else "1"
        console.print(f"  • Current phase: Phase {phase_num}")

    console.print()
