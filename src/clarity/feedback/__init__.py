"""
Feedback and scoring display for MVP1.

Renders scorecards, tips, trends, and progress tracking.
"""

from clarity.feedback.progress import (
    calculate_phase_metrics,
    detect_overcorrection,
    display_phase_milestone,
    prompt_comfort_rating,
)
from clarity.feedback.scorecard import (
    display_composite_only,
    display_scorecard,
    get_rating_from_score,
    get_score_color,
    render_scorecard_table,
)
from clarity.feedback.tips import display_tips, display_tips_compact, format_tip
from clarity.feedback.trends import (
    TrendComparison,
    calculate_trends,
    check_personal_best,
    display_personal_bests,
    display_trends,
)

__all__ = [
    # Scorecard
    "display_scorecard",
    "render_scorecard_table",
    "display_composite_only",
    "get_score_color",
    "get_rating_from_score",
    # Tips
    "display_tips",
    "display_tips_compact",
    "format_tip",
    # Trends
    "calculate_trends",
    "display_trends",
    "TrendComparison",
    "check_personal_best",
    "display_personal_bests",
    # Progress
    "display_phase_milestone",
    "detect_overcorrection",
    "prompt_comfort_rating",
    "calculate_phase_metrics",
]
