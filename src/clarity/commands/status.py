"""
Status command - current phase and progress (Ticket 1.6.5).

Shows phase, streak, progress toward next phase, focus areas.
"""

from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from clarity.feedback import calculate_phase_metrics
from clarity.session import detect_current_phase, get_phase_config
from clarity.storage import StorageManager


def run_status() -> None:
    """
    Display current status: phase, streak, progress, focus areas.
    """
    console = Console()
    storage = StorageManager()

    data = storage.read_all()
    sessions = data.get("sessions", [])

    if not sessions:
        console.print("\n[yellow]No sessions yet. Run 'clarity practice' to start![/yellow]\n")
        return

    # === BASIC INFO ===
    current_phase = detect_current_phase(storage)
    phase_config = get_phase_config(current_phase)
    total_sessions = len(sessions)

    # === STREAK CALCULATION ===
    streak = calculate_streak(sessions)

    # === PHASE PROGRESS ===
    sessions_in_phase = len([s for s in sessions if s.get("phase") == current_phase.name])

    # Calculate recent metrics
    phase_metrics = calculate_phase_metrics(sessions, current_phase)

    # Check transition criteria
    criteria_met = 0
    total_criteria = len(phase_config.transition_criteria)

    for metric_name, threshold in phase_config.transition_criteria.items():
        current_value = phase_metrics.get(metric_name, 0)

        # Check if met
        if metric_name in ["filler_rate", "maze_rate", "hedging_frequency"]:
            met = current_value <= threshold
        else:
            met = current_value >= threshold

        if met:
            criteria_met += 1

    # Determine readiness
    ready_to_advance = (
        sessions_in_phase >= phase_config.min_sessions and criteria_met == total_criteria
    )

    # === RECENT PERFORMANCE ===
    recent_5 = sessions[-5:] if len(sessions) >= 5 else sessions
    avg_recent_score = (
        sum(s.get("metrics", {}).get("composite_score", 0) for s in recent_5) / len(recent_5)
        if recent_5
        else 0
    )

    # === BUILD DISPLAY ===
    content = Text()

    # Header
    content.append("📊 Your Progress Status\n\n", style="bold cyan")

    # Phase info
    content.append(f"Phase: {current_phase.value}\n", style="bold white")
    content.append(f"  • {phase_config.description}\n", style="dim")
    content.append(f"  • Sessions in phase: {sessions_in_phase}/{phase_config.min_sessions}\n")
    content.append(f"  • Criteria met: {criteria_met}/{total_criteria}\n")

    if ready_to_advance:
        content.append("\n🎉 Ready to advance to next phase!\n", style="bold green")
    else:
        sessions_remaining = max(0, phase_config.min_sessions - sessions_in_phase)
        if sessions_remaining > 0:
            content.append(
                f"\n{sessions_remaining} more sessions to unlock advancement.\n", style="yellow"
            )
        else:
            content.append(
                f"\nMeet {total_criteria - criteria_met} more criteria to advance.\n",
                style="yellow",
            )

    # Streak
    content.append("\n")
    content.append(f"🔥 Current Streak: {streak} days\n", style="bold")

    # Overall stats
    content.append("\n")
    content.append("Overall Statistics:\n", style="bold")
    content.append(f"  • Total sessions: {total_sessions}\n")
    content.append(f"  • Recent average score: {avg_recent_score:.1f}/100\n")

    # Last session date
    if sessions:
        last_session = sessions[-1]
        timestamp = last_session.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            last_date = dt.strftime("%Y-%m-%d %H:%M")
            content.append(f"  • Last session: {last_date}\n")
        except (ValueError, AttributeError):
            pass

    # Active focus areas (from phase config)
    content.append("\n")
    content.append("Active Dimensions:\n", style="bold")
    for dim, weight in phase_config.dimension_weights.items():
        if weight > 0:
            content.append(f"  • {dim}\n")

    panel = Panel(
        content,
        title="[bold]Status Report[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def calculate_streak(sessions: list[dict]) -> int:
    """
    Calculate current daily streak.

    Args:
        sessions: List of session dicts

    Returns:
        Number of consecutive days with sessions
    """
    if not sessions:
        return 0

    # Get dates of all sessions (just the date part, ignore time)
    session_dates = set()
    for session in sessions:
        timestamp = session.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            session_dates.add(dt.date())
        except (ValueError, AttributeError):
            continue

    if not session_dates:
        return 0

    # Sort dates
    sorted_dates = sorted(session_dates, reverse=True)

    # Check if most recent session was today or yesterday
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    if sorted_dates[0] not in [today, yesterday]:
        return 0  # Streak broken

    # Count consecutive days
    streak = 0
    expected_date = sorted_dates[0]

    for date in sorted_dates:
        if date == expected_date:
            streak += 1
            expected_date = date - timedelta(days=1)
        else:
            break

    return streak
