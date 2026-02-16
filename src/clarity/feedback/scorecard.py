"""
Scorecard rendering (Ticket 1.5.1).

Displays dimension scores in rich tables with color coding and ratings.
"""

from rich.console import Console
from rich.table import Table

from clarity.analysis.models import AnalysisResult
from clarity.session.phase_config import Phase, PhaseConfig


def get_score_color(score: int) -> str:
    """
    Get color for score based on thresholds.

    Args:
        score: Score 0-100

    Returns:
        Color name for rich formatting
    """
    if score >= 75:
        return "green"
    elif score >= 50:
        return "yellow"
    else:
        return "red"


def get_rating_from_score(score: int) -> str:
    """
    Convert numeric score to rating label.

    Args:
        score: Score 0-100

    Returns:
        Rating label (Excellent/Strong/Competent/Developing)
    """
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Strong"
    elif score >= 50:
        return "Competent"
    else:
        return "Developing"


def render_scorecard_table(
    result: AnalysisResult,
    phase_config: PhaseConfig,
) -> Table:
    """
    Render scorecard as rich Table.

    Args:
        result: AnalysisResult with scores
        phase_config: PhaseConfig for active dimensions

    Returns:
        Rich Table object
    """
    table = Table(title="📊 Session Scorecard", show_header=True, header_style="bold")

    table.add_column("Dimension", style="cyan", width=25)
    table.add_column("Score", justify="right", width=8)
    table.add_column("Rating", width=12)
    table.add_column("Feedback", width=50)

    # Add dimension rows (phase-gated)
    for dim_score in result.dimension_scores:
        score_color = get_score_color(dim_score.score)
        rating_color = score_color

        table.add_row(
            dim_score.dimension,
            f"[{score_color}]{dim_score.score}/100[/{score_color}]",
            f"[{rating_color}]{dim_score.rating}[/{rating_color}]",
            dim_score.feedback,
        )

    # Add separator
    table.add_row("", "", "", "")

    # Add composite score
    composite_color = get_score_color(result.composite_score)
    table.add_row(
        "[bold]Composite Score[/bold]",
        f"[bold {composite_color}]{result.composite_score}/100[/bold {composite_color}]",
        f"[bold]{get_rating_from_score(result.composite_score)}[/bold]",
        "Overall weighted average",
        style="bold",
    )

    return table


def display_scorecard(
    result: AnalysisResult,
    phase_config: PhaseConfig,
    console: Console | None = None,
) -> None:
    """
    Display full scorecard with scores and metrics.

    Args:
        result: AnalysisResult with scores
        phase_config: PhaseConfig for context
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    # Render table
    table = render_scorecard_table(result, phase_config)
    console.print()
    console.print(table)
    console.print()

    # Display key metrics summary
    console.print("[bold cyan]Key Metrics:[/bold cyan]")
    console.print(f"  • Speaking rate: {result.speaking_rate_wpm:.1f} WPM")
    console.print(
        f"  • Filler rate: {result.filler_rate:.1f}/min ({result.filler_percentage:.1f}% of words)"
    )
    console.print(
        f"  • Framework: {result.framework_used} — {'✓ Complete' if result.framework_completion else '✗ Incomplete'}"
    )

    # Phase-specific metrics
    if phase_config.phase in [Phase.PHASE_2, Phase.PHASE_3]:
        if result.maze_rate is not None:
            console.print(f"  • Maze rate: {result.maze_rate:.1f}/min")
        if result.hedging_rate is not None:
            console.print(f"  • Hedging rate: {result.hedging_rate:.1f}/min")

    if phase_config.phase == Phase.PHASE_3:
        if result.pause_quality_score is not None:
            console.print(f"  • Pause quality: {result.pause_quality_score}/100")

    console.print()


def display_composite_only(
    result: AnalysisResult,
    console: Console | None = None,
) -> None:
    """
    Display just the composite score (for quick summaries).

    Args:
        result: AnalysisResult
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    color = get_score_color(result.composite_score)
    rating = get_rating_from_score(result.composite_score)

    console.print(
        f"[bold]Session Score:[/bold] [{color}]{result.composite_score}/100[/{color}] — {rating}"
    )
