"""
Tip formatting and display (Ticket 1.5.2).

Displays actionable improvement tips with rich panels.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from clarity.analysis.models import Tip


def format_tip(tip: Tip, tip_number: int) -> Panel:
    """
    Format a single tip as a rich Panel.

    Args:
        tip: Tip object
        tip_number: Tip number (1, 2, 3)

    Returns:
        Rich Panel with formatted tip
    """
    content = Text()

    # Title
    content.append(f"💡 {tip.title}\n\n", style="bold yellow")

    # Explanation
    content.append(tip.explanation, style="white")
    content.append("\n")

    # Transcript excerpt (if available)
    if tip.transcript_excerpt:
        content.append("\n")
        content.append("Example from your speech:\n", style="dim")
        content.append(f'"{tip.transcript_excerpt}"\n', style="italic")

    # Technique (if available)
    if tip.technique:
        content.append("\n")
        content.append("Try this: ", style="bold green")
        content.append(tip.technique, style="green")

    panel = Panel(
        content,
        title=f"[bold]Tip #{tip_number}[/bold]",
        border_style="yellow",
        padding=(1, 2),
    )

    return panel


def display_tips(
    tips: list[Tip],
    console: Console | None = None,
) -> None:
    """
    Display all tips with formatting.

    Args:
        tips: List of Tip objects (typically top 3)
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    console.print()
    console.print("[bold cyan]🎯 Actionable Tips for Improvement[/bold cyan]")
    console.print()

    for i, tip in enumerate(tips[:3], start=1):  # Show max 3 tips
        panel = format_tip(tip, i)
        console.print(panel)
        if i < len(tips):
            console.print()  # Spacing between tips

    console.print()


def display_tips_compact(
    tips: list[Tip],
    console: Console | None = None,
) -> None:
    """
    Display tips in compact format (for summaries).

    Args:
        tips: List of Tip objects
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    console.print("[bold cyan]Top Tips:[/bold cyan]")
    for i, tip in enumerate(tips[:3], start=1):
        console.print(f"  {i}. [yellow]{tip.title}[/yellow]: {tip.explanation[:80]}...")
    console.print()
