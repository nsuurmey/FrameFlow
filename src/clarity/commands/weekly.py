"""
Weekly command - aggregate weekly summary (Ticket 1.6.6).

Shows sessions completed, avg scores, best/worst dimensions, streak.
"""

from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from clarity.feedback import get_score_color
from clarity.storage import StorageManager


def run_weekly() -> None:
    """
    Display weekly summary report.
    """
    console = Console()
    storage = StorageManager()

    data = storage.read_all()
    sessions = data.get("sessions", [])

    if not sessions:
        console.print("\n[yellow]No sessions found. Run 'clarity practice' to start![/yellow]\n")
        return

    # Get current week's sessions (last 7 days)
    today = datetime.now().date()
    week_start = today - timedelta(days=6)  # Last 7 days including today

    weekly_sessions = []
    for session in sessions:
        timestamp = session.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if dt.date() >= week_start:
                weekly_sessions.append(session)
        except (ValueError, AttributeError):
            continue

    if not weekly_sessions:
        console.print(
            f"\n[yellow]No sessions in the last 7 days (since {week_start}).[/yellow]\n"
        )
        return

    # === CALCULATE STATS ===

    # Average scores by dimension
    dimension_totals: dict[str, list[int]] = {}
    composite_scores = []

    for session in weekly_sessions:
        metrics = session.get("metrics", {})
        composite_scores.append(metrics.get("composite_score", 0))

        analysis = session.get("analysis", {})
        for ds in analysis.get("dimension_scores", []):
            dim_name = ds.get("dimension", "Unknown")
            score = ds.get("score", 0)

            if dim_name not in dimension_totals:
                dimension_totals[dim_name] = []
            dimension_totals[dim_name].append(score)

    # Calculate averages
    avg_composite = sum(composite_scores) / len(composite_scores) if composite_scores else 0

    dimension_avgs = {}
    for dim, scores in dimension_totals.items():
        dimension_avgs[dim] = sum(scores) / len(scores) if scores else 0

    # Find best and worst dimensions
    if dimension_avgs:
        best_dim = max(dimension_avgs.items(), key=lambda x: x[1])
        worst_dim = min(dimension_avgs.items(), key=lambda x: x[1])
    else:
        best_dim = ("None", 0)
        worst_dim = ("None", 0)

    # Streak
    from clarity.commands.status import calculate_streak

    streak = calculate_streak(sessions)

    # === BUILD DISPLAY ===
    content = Text()

    # Header
    content.append("📅 Weekly Summary Report\n\n", style="bold cyan")
    content.append(f"Week: {week_start} to {today}\n\n", style="dim")

    # Overview
    content.append("Overview:\n", style="bold")
    content.append(f"  • Sessions completed: {len(weekly_sessions)}\n")

    avg_color = get_score_color(int(avg_composite))
    content.append("  • Average score: ", style="white")
    content.append(f"{avg_composite:.1f}/100\n", style=avg_color)

    content.append(f"  • Current streak: {streak} days\n")

    # Dimensions
    if dimension_avgs:
        content.append("\n")
        content.append("Dimension Performance:\n", style="bold")

        # Table
        dim_table = Table(show_header=True, box=None, padding=(0, 2))
        dim_table.add_column("Dimension", style="cyan")
        dim_table.add_column("Avg Score", justify="right")
        dim_table.add_column("Sessions", justify="right")

        for dim, avg_score in sorted(dimension_avgs.items(), key=lambda x: x[1], reverse=True):
            score_color = get_score_color(int(avg_score))
            session_count = len(dimension_totals[dim])

            dim_table.add_row(
                dim,
                f"[{score_color}]{avg_score:.1f}[/{score_color}]",
                str(session_count),
            )

        content.append("\n")
        # Can't directly append table to Text, will print separately

    # Best/worst
    content.append("\n")
    content.append("Highlights:\n", style="bold")
    content.append(f"  • Strongest dimension: [green]{best_dim[0]}[/green] ({best_dim[1]:.1f})\n")
    content.append(f"  • Focus area: [yellow]{worst_dim[0]}[/yellow] ({worst_dim[1]:.1f})\n")

    # Recent topics
    if weekly_sessions:
        content.append("\n")
        content.append("Topics covered:\n", style="bold")
        topics = [s.get("topic", "Unknown")[:40] for s in weekly_sessions[-5:]]
        for topic in topics:
            content.append(f"  • {topic}\n", style="dim")

    panel = Panel(
        content,
        title="[bold]Weekly Report[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)

    # Print dimension table if exists
    if dimension_avgs:
        console.print()
        console.print(dim_table)

    console.print()
