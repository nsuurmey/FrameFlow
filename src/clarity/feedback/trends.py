"""
Trend comparison and progress tracking (Ticket 1.5.3).

Compares current session to baseline and recent sessions.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from clarity.analysis.models import AnalysisResult


@dataclass
class TrendComparison:
    """Comparison of current session to historical data."""

    metric_name: str
    current_value: float
    baseline_value: float | None
    recent_average: float | None
    delta_from_baseline: float | None
    delta_from_recent: float | None
    is_improvement: bool | None  # True if delta is positive direction


def calculate_trends(
    current_result: AnalysisResult,
    baseline_metrics: dict | None,
    recent_sessions: list[dict],
) -> list[TrendComparison]:
    """
    Calculate trend comparisons for key metrics.

    Args:
        current_result: Current session's AnalysisResult
        baseline_metrics: User's baseline metrics (optional)
        recent_sessions: Last 5 sessions data

    Returns:
        List of TrendComparison objects
    """
    trends = []

    # Key metrics to track
    metrics_config = [
        ("composite_score", "Composite Score", False),  # Higher is better
        ("filler_rate", "Filler Rate", True),  # Lower is better
        ("speaking_rate_wpm", "Speaking Rate (WPM)", False),  # Target range
    ]

    for metric_key, metric_name, lower_is_better in metrics_config:
        # Get current value
        current_value = getattr(current_result, metric_key)

        # Get baseline value
        baseline_value = None
        if baseline_metrics and metric_key in baseline_metrics:
            baseline_value = baseline_metrics[metric_key]

        # Calculate recent average
        recent_average = None
        if recent_sessions:
            values = []
            for session in recent_sessions:
                metrics = session.get("metrics", {})
                if metric_key in metrics:
                    values.append(metrics[metric_key])

            if values:
                recent_average = sum(values) / len(values)

        # Calculate deltas
        delta_from_baseline = None
        if baseline_value is not None:
            delta_from_baseline = current_value - baseline_value

        delta_from_recent = None
        if recent_average is not None:
            delta_from_recent = current_value - recent_average

        # Determine if improvement
        is_improvement = None
        if delta_from_recent is not None:
            if lower_is_better:
                is_improvement = delta_from_recent < 0
            else:
                is_improvement = delta_from_recent > 0

        trends.append(
            TrendComparison(
                metric_name=metric_name,
                current_value=current_value,
                baseline_value=baseline_value,
                recent_average=recent_average,
                delta_from_baseline=delta_from_baseline,
                delta_from_recent=delta_from_recent,
                is_improvement=is_improvement,
            )
        )

    return trends


def display_trends(
    trends: list[TrendComparison],
    console: Console | None = None,
) -> None:
    """
    Display trend comparison table.

    Args:
        trends: List of TrendComparison objects
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    table = Table(title="📈 Progress Tracking", show_header=True, header_style="bold")

    table.add_column("Metric", style="cyan")
    table.add_column("Current", justify="right")
    table.add_column("vs Baseline", justify="right")
    table.add_column("vs Recent", justify="right")
    table.add_column("Trend", justify="center")

    for trend in trends:
        # Format current value
        current_str = f"{trend.current_value:.1f}"

        # Format baseline delta
        baseline_str = "—"
        if trend.delta_from_baseline is not None:
            sign = "+" if trend.delta_from_baseline > 0 else ""
            baseline_str = f"{sign}{trend.delta_from_baseline:.1f}"

        # Format recent delta
        recent_str = "—"
        if trend.delta_from_recent is not None:
            sign = "+" if trend.delta_from_recent > 0 else ""
            recent_str = f"{sign}{trend.delta_from_recent:.1f}"

        # Trend arrow
        trend_str = "—"
        if trend.is_improvement is not None:
            if trend.is_improvement:
                trend_str = "[green]↑[/green]"
            else:
                trend_str = "[red]↓[/red]"

        table.add_row(
            trend.metric_name,
            current_str,
            baseline_str,
            recent_str,
            trend_str,
        )

    console.print()
    console.print(table)
    console.print()


def check_personal_best(
    current_result: AnalysisResult,
    all_sessions: list[dict],
) -> list[str]:
    """
    Check for personal bests in any dimension.

    Args:
        current_result: Current session's AnalysisResult
        all_sessions: All session history

    Returns:
        List of dimension names where personal best was achieved
    """
    personal_bests = []

    # Check composite score
    max_composite = current_result.composite_score
    for session in all_sessions:
        metrics = session.get("metrics", {})
        if metrics.get("composite_score", 0) > max_composite:
            max_composite = metrics["composite_score"]

    if current_result.composite_score >= max_composite:
        personal_bests.append("Composite Score")

    # Check each dimension
    for dim_score in current_result.dimension_scores:
        max_score = dim_score.score
        for session in all_sessions:
            analysis = session.get("analysis", {})
            dim_scores = analysis.get("dimension_scores", [])
            for prev_dim in dim_scores:
                if prev_dim.get("dimension") == dim_score.dimension:
                    if prev_dim.get("score", 0) > max_score:
                        max_score = prev_dim["score"]

        if dim_score.score >= max_score and dim_score.score >= 75:
            personal_bests.append(dim_score.dimension)

    return personal_bests


def display_personal_bests(
    personal_bests: list[str],
    console: Console | None = None,
) -> None:
    """
    Display personal best achievements.

    Args:
        personal_bests: List of dimension names
        console: Rich Console instance
    """
    if not personal_bests:
        return

    if console is None:
        console = Console()

    console.print()
    console.print("[bold green]🏆 Personal Best![/bold green]")
    for dimension in personal_bests:
        console.print(f"  • {dimension}")
    console.print()
