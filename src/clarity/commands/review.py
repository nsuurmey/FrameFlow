"""
Review command - re-display past session (Ticket 1.6.4).

Shows full scorecard, tips, and transcript from a specific session.
"""

from datetime import datetime

from rich.console import Console

from clarity.analysis.models import AnalysisResult, DimensionScore, Tip
from clarity.feedback import display_scorecard, display_tips
from clarity.session import get_phase_config
from clarity.session.phase_config import Phase
from clarity.storage import StorageManager


def run_review(session_id: str | int, export: bool = False) -> None:
    """
    Review a past session with full details.

    Args:
        session_id: Session number (1-indexed) or "last"
        export: If True, export to markdown file
    """
    console = Console()
    storage = StorageManager()

    data = storage.read_all()
    sessions = data.get("sessions", [])

    if not sessions:
        console.print("\n[red]No sessions found.[/red]\n")
        return

    # Resolve session ID
    if session_id == "last":
        session_idx = len(sessions) - 1
        session_num = len(sessions)
    else:
        try:
            session_num = int(session_id)
            session_idx = session_num - 1
        except ValueError:
            console.print(f"\n[red]Invalid session ID: {session_id}[/red]")
            console.print("Use a number (1, 2, 3...) or 'last'\n")
            return

    # Validate range
    if session_idx < 0 or session_idx >= len(sessions):
        console.print(f"\n[red]Session #{session_num} not found.[/red]")
        console.print(f"Valid range: 1-{len(sessions)}\n")
        return

    session = sessions[session_idx]

    # === HEADER ===
    console.print()
    console.print(f"[bold cyan]═══ Session #{session_num} Review ═══[/bold cyan]")
    console.print()

    # === METADATA ===
    timestamp = session.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        date_str = "Unknown"

    topic = session.get("topic", "Unknown")
    framework = session.get("framework", "Unknown")
    phase_name = session.get("phase", "PHASE_1")

    console.print(f"[bold]Date:[/bold] {date_str}")
    console.print(f"[bold]Topic:[/bold] {topic}")
    console.print(f"[bold]Framework:[/bold] {framework}")
    console.print(f"[bold]Phase:[/bold] {phase_name}")
    console.print()

    # === RECONSTRUCT AnalysisResult ===
    metrics = session.get("metrics", {})
    analysis = session.get("analysis", {})

    # Dimension scores
    dimension_scores = []
    for ds_data in analysis.get("dimension_scores", []):
        dimension_scores.append(
            DimensionScore(
                dimension=ds_data.get("dimension", "Unknown"),
                score=ds_data.get("score", 0),
                rating=ds_data.get("rating", "Developing"),
                feedback=ds_data.get("feedback", ""),
            )
        )

    # Tips
    tips = []
    for tip_data in analysis.get("tips", []):
        tips.append(
            Tip(
                title=tip_data.get("title", ""),
                explanation=tip_data.get("explanation", ""),
                transcript_excerpt=tip_data.get("transcript_excerpt"),
                technique=tip_data.get("technique"),
            )
        )

    # Build AnalysisResult
    result = AnalysisResult(
        composite_score=metrics.get("composite_score", 0),
        dimension_scores=dimension_scores,
        filler_count=metrics.get("filler_count", 0),
        filler_rate=metrics.get("filler_rate", 0),
        filler_percentage=metrics.get("filler_percentage", 0),
        speaking_rate_wpm=metrics.get("speaking_rate_wpm", 0),
        framework_used=framework,
        framework_completion=metrics.get("framework_completion", 0) == 100,
        tips=tips,
        maze_count=metrics.get("maze_count"),
        maze_rate=metrics.get("maze_rate"),
        hedging_count=metrics.get("hedging_count"),
        hedging_rate=metrics.get("hedging_rate"),
        pause_quality_score=metrics.get("pause_quality_score"),
    )

    # Get phase config
    try:
        phase = Phase[phase_name]
    except (KeyError, ValueError):
        phase = Phase.PHASE_1

    phase_config = get_phase_config(phase)

    # === DISPLAY SCORECARD ===
    display_scorecard(result, phase_config, console)

    # === DISPLAY TIPS ===
    if tips:
        display_tips(tips, console)

    # === TRANSCRIPT ===
    transcript = session.get("transcript", "")
    if transcript:
        console.print("[bold cyan]═══ Transcript ═══[/bold cyan]")
        console.print()

        # Truncate if too long
        if len(transcript) > 1000:
            console.print(transcript[:1000])
            console.print("\n[dim]... (truncated, full transcript in export)[/dim]")
        else:
            console.print(transcript)

        console.print()

    # === EXPORT ===
    if export:
        export_path = f"session_{session_num}_review.md"
        _export_to_markdown(session, session_num, result, export_path)
        console.print(f"[green]✓ Exported to {export_path}[/green]\n")


def _export_to_markdown(
    session: dict,
    session_num: int,
    result: AnalysisResult,
    output_path: str,
) -> None:
    """
    Export session review to markdown file.

    Args:
        session: Session dict
        session_num: Session number
        result: AnalysisResult object
        output_path: Output file path
    """
    lines = []

    # Header
    lines.append(f"# Session #{session_num} Review")
    lines.append("")

    # Metadata
    timestamp = session.get("timestamp", "")
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        date_str = "Unknown"

    lines.append(f"**Date:** {date_str}")
    lines.append(f"**Topic:** {session.get('topic', 'Unknown')}")
    lines.append(f"**Framework:** {session.get('framework', 'Unknown')}")
    lines.append(f"**Phase:** {session.get('phase', 'Unknown')}")
    lines.append("")

    # Composite score
    lines.append("## Overall Score")
    lines.append("")
    lines.append(f"**{result.composite_score}/100**")
    lines.append("")

    # Dimension scores
    lines.append("## Dimension Scores")
    lines.append("")
    for ds in result.dimension_scores:
        lines.append(f"### {ds.dimension}: {ds.score}/100 ({ds.rating})")
        lines.append("")
        lines.append(ds.feedback)
        lines.append("")

    # Tips
    if result.tips:
        lines.append("## Actionable Tips")
        lines.append("")
        for i, tip in enumerate(result.tips, 1):
            lines.append(f"### Tip {i}: {tip.title}")
            lines.append("")
            lines.append(tip.explanation)
            lines.append("")
            if tip.transcript_excerpt:
                lines.append(f"> {tip.transcript_excerpt}")
                lines.append("")
            if tip.technique:
                lines.append(f"**Technique:** {tip.technique}")
                lines.append("")

    # Transcript
    transcript = session.get("transcript", "")
    if transcript:
        lines.append("## Transcript")
        lines.append("")
        lines.append(transcript)
        lines.append("")

    # Write file
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
