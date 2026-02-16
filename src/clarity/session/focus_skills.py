"""
Focus skill selection (Ticket 1.3.5).

Selects 1-2 focus skills from phase-appropriate pool, weighted toward
user's weakest dimensions from last 5 sessions.
"""

import random
from collections import Counter

from clarity.session.phase_config import PhaseConfig


def select_focus_skills(
    config: PhaseConfig,
    storage_manager,
    num_skills: int = 2,
) -> list[str]:
    """
    Select focus skills for a session.

    Weighted toward user's weakest dimensions based on recent sessions.

    Args:
        config: PhaseConfig with available_focus_skills
        storage_manager: StorageManager for accessing session history
        num_skills: Number of skills to select (default: 2)

    Returns:
        List of selected focus skill names

    Examples:
        >>> skills = select_focus_skills(PHASE_1_CONFIG, storage, num_skills=2)
        >>> len(skills)
        2
    """
    available_skills = config.available_focus_skills

    if num_skills >= len(available_skills):
        # Return all available skills
        return available_skills

    # Get recent session data
    try:
        recent_sessions = storage_manager.get_recent_sessions(n=5)
    except Exception:
        # No session history - select randomly
        return random.sample(available_skills, num_skills)

    if not recent_sessions:
        # No history - select randomly
        return random.sample(available_skills, num_skills)

    # Analyze weakest dimensions from recent sessions
    weak_areas = _identify_weak_dimensions(recent_sessions, config)

    # Map weak dimensions to focus skills
    weighted_skills = _map_dimensions_to_skills(weak_areas, available_skills)

    if not weighted_skills:
        # No mapping found - select randomly
        return random.sample(available_skills, num_skills)

    # Select top skills (weighted by weakness)
    selected = weighted_skills[:num_skills]

    # If we don't have enough, fill with random selections
    if len(selected) < num_skills:
        remaining = [s for s in available_skills if s not in selected]
        selected.extend(random.sample(remaining, num_skills - len(selected)))

    return selected


def _identify_weak_dimensions(
    sessions: list[dict], config: PhaseConfig
) -> list[str]:
    """
    Identify weak dimensions from recent sessions.

    Analyzes metrics from last N sessions and returns dimensions that
    are below target thresholds.

    Args:
        sessions: List of session dictionaries
        config: PhaseConfig with active_metrics

    Returns:
        List of dimension names that need improvement (ordered by weakness)
    """
    weak_dimensions = []

    # Metric thresholds (lower scores = weaker performance)
    metric_thresholds = {
        "filler_rate": 5.0,  # Higher is worse
        "filler_percentage": 3.0,  # Higher is worse
        "maze_rate": 2.0,  # Higher is worse
        "speaking_rate_wpm": 130.0,  # Lower is worse
        "framework_completion": 80.0,  # Lower is worse
        "sentence_completion_rate": 90.0,  # Lower is worse
    }

    # Analyze each metric
    for metric in config.active_metrics:
        if metric not in metric_thresholds:
            continue

        # Extract metric values from sessions
        values = []
        for session in sessions:
            metrics_data = session.get("metrics", {})
            if metric in metrics_data:
                values.append(metrics_data[metric])

        if not values:
            continue

        avg_value = sum(values) / len(values)

        # Check if below threshold
        # Note: Some metrics are "higher is worse" (filler_rate, maze_rate)
        if metric in ["filler_rate", "filler_percentage", "maze_rate"]:
            if avg_value > metric_thresholds[metric]:
                weak_dimensions.append(metric)
        else:
            if avg_value < metric_thresholds[metric]:
                weak_dimensions.append(metric)

    return weak_dimensions


def _map_dimensions_to_skills(
    weak_dimensions: list[str], available_skills: list[str]
) -> list[str]:
    """
    Map weak dimensions to focus skills.

    Args:
        weak_dimensions: List of metrics that need improvement
        available_skills: Available focus skills for this phase

    Returns:
        List of skills to focus on (ordered by priority)
    """
    # Mapping of metrics to focus skills
    dimension_skill_map = {
        "filler_rate": [
            "Filler awareness",
            "Filler reduction (active replacement)",
            "Pause replacement",
        ],
        "filler_percentage": [
            "Filler awareness",
            "Filler reduction (active replacement)",
        ],
        "maze_rate": ["Cognitive flexibility", "Framework adherence"],
        "speaking_rate_wpm": ["Pacing control"],
        "framework_completion": ["Framework adherence", "Framework rotation"],
        "sentence_completion_rate": ["Conciseness", "Cognitive flexibility"],
        "hedging_frequency": ["Hedging elimination"],
        "pause_quality": ["Strategic pausing"],
    }

    # Collect recommended skills
    skill_recommendations = []
    for dimension in weak_dimensions:
        if dimension in dimension_skill_map:
            skill_recommendations.extend(dimension_skill_map[dimension])

    # Count recommendations (for weighting)
    skill_counts = Counter(skill_recommendations)

    # Filter to available skills and sort by frequency
    weighted_skills = [
        skill
        for skill, count in skill_counts.most_common()
        if skill in available_skills
    ]

    return weighted_skills


def get_skill_description(skill_name: str) -> str:
    """
    Get description for a focus skill.

    Args:
        skill_name: Name of the skill

    Returns:
        Description of what to focus on
    """
    descriptions = {
        "Filler awareness": "Notice when you're about to say a filler word",
        "Filler reduction (active replacement)": "Replace fillers with intentional pauses",
        "Framework adherence": "Hit all framework components in order",
        "Pause replacement": "Use silence instead of um/uh",
        "Clear articulation": "Enunciate clearly and maintain steady pace",
        "Vocal variety": "Vary pitch, pace, and volume for emphasis",
        "Strategic pausing": "Pause at syntactic boundaries (commas, periods)",
        "Pacing control": "Maintain 130-160 WPM with intentional variation",
        "Framework rotation": "Quickly choose appropriate framework for topic",
        "Topic complexity handling": "Organize complex ideas clearly",
        "Conciseness": "Eliminate unnecessary words and hedging",
        "Cognitive flexibility": "Adapt structure mid-speech if needed",
        "Hedging elimination": "Remove qualifiers like 'kind of', 'sort of'",
        "Strong openings": "Lead with main point (BLUF - Bottom Line Up Front)",
        "Strong closings": "End with clear call-to-action or takeaway",
        "Zero-prep confidence": "Speak coherently without preparation",
        "Pressure handling": "Maintain clarity under time pressure",
    }

    return descriptions.get(skill_name, "Focus on this skill during practice")
