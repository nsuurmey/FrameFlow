"""
Data models for analysis results (Ticket 1.4.5).

Structures for parsing Claude API responses into typed dataclasses.
"""

from dataclasses import dataclass


@dataclass
class DimensionScore:
    """Score for a single speaking dimension."""

    dimension: str  # e.g., "Filler Frequency"
    score: int  # 0-100
    rating: str  # Developing/Competent/Strong/Excellent
    feedback: str  # Dimension-specific feedback


@dataclass
class Tip:
    """Actionable improvement tip."""

    title: str
    explanation: str
    transcript_excerpt: str | None = None
    technique: str | None = None


@dataclass
class AnalysisResult:
    """
    Complete analysis result from Claude API.

    Contains scores, tips, and metadata from transcript analysis.
    """

    # Dimension scores
    dimension_scores: list[DimensionScore]

    # Composite score (weighted average)
    composite_score: int

    # Actionable tips (top 3)
    tips: list[Tip]

    # Framework completion
    framework_used: str
    framework_completion: bool
    missing_components: list[str]

    # Filler analysis
    filler_count: int
    filler_rate: float  # Per minute
    filler_percentage: float  # Percentage of total words

    # Speaking metrics
    word_count: int
    duration_seconds: float
    speaking_rate_wpm: float

    # Additional metrics (phase-dependent)
    maze_count: int | None = None
    maze_rate: float | None = None
    hedging_count: int | None = None
    hedging_rate: float | None = None
    pause_quality_score: int | None = None

    # Raw response (for debugging)
    raw_response: dict | None = None


def parse_analysis_response(response: dict) -> AnalysisResult:
    """
    Parse Claude API JSON response into AnalysisResult.

    Args:
        response: JSON dict from Claude API

    Returns:
        AnalysisResult with parsed data

    Raises:
        KeyError: If required fields are missing
        ValueError: If data validation fails
    """
    # Parse dimension scores
    dimension_scores = []
    for dim_data in response.get("dimension_scores", []):
        dimension_scores.append(
            DimensionScore(
                dimension=dim_data["dimension"],
                score=dim_data["score"],
                rating=dim_data["rating"],
                feedback=dim_data["feedback"],
            )
        )

    # Parse tips
    tips = []
    for tip_data in response.get("tips", []):
        tips.append(
            Tip(
                title=tip_data["title"],
                explanation=tip_data["explanation"],
                transcript_excerpt=tip_data.get("transcript_excerpt"),
                technique=tip_data.get("technique"),
            )
        )

    # Parse framework completion
    framework_data = response.get("framework_analysis", {})

    # Build result
    result = AnalysisResult(
        dimension_scores=dimension_scores,
        composite_score=response["composite_score"],
        tips=tips,
        framework_used=framework_data.get("framework_used", "PREP"),
        framework_completion=framework_data.get("completion", False),
        missing_components=framework_data.get("missing_components", []),
        filler_count=response["filler_count"],
        filler_rate=response["filler_rate"],
        filler_percentage=response["filler_percentage"],
        word_count=response["word_count"],
        duration_seconds=response["duration_seconds"],
        speaking_rate_wpm=response["speaking_rate_wpm"],
        maze_count=response.get("maze_count"),
        maze_rate=response.get("maze_rate"),
        hedging_count=response.get("hedging_count"),
        hedging_rate=response.get("hedging_rate"),
        pause_quality_score=response.get("pause_quality_score"),
        raw_response=response,
    )

    return result


def validate_analysis_response(response: dict) -> list[str]:
    """
    Validate that response contains all required fields.

    Args:
        response: JSON dict from Claude API

    Returns:
        List of missing or invalid fields (empty if valid)
    """
    errors = []

    # Required top-level fields
    required_fields = [
        "dimension_scores",
        "composite_score",
        "tips",
        "filler_count",
        "filler_rate",
        "filler_percentage",
        "word_count",
        "duration_seconds",
        "speaking_rate_wpm",
    ]

    for field in required_fields:
        if field not in response:
            errors.append(f"Missing required field: {field}")

    # Validate dimension_scores structure
    if "dimension_scores" in response:
        for i, dim in enumerate(response["dimension_scores"]):
            if "dimension" not in dim:
                errors.append(f"dimension_scores[{i}]: missing 'dimension'")
            if "score" not in dim:
                errors.append(f"dimension_scores[{i}]: missing 'score'")
            elif not isinstance(dim["score"], int) or not 0 <= dim["score"] <= 100:
                errors.append(f"dimension_scores[{i}]: invalid score (must be 0-100)")

    # Validate tips structure
    if "tips" in response:
        for i, tip in enumerate(response["tips"]):
            if "title" not in tip:
                errors.append(f"tips[{i}]: missing 'title'")
            if "explanation" not in tip:
                errors.append(f"tips[{i}]: missing 'explanation'")

    # Validate composite_score
    if "composite_score" in response:
        if not isinstance(response["composite_score"], int) or not 0 <= response["composite_score"] <= 100:
            errors.append("composite_score: must be integer 0-100")

    return errors
