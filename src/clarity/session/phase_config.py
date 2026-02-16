"""
Phase configuration data models (Ticket 1.3.1).

Defines dataclasses for Phase 1/2/3 with all configuration values
from PRD: metrics, frameworks, topic types, prep time, speaking duration,
warm-up exercises, and transition thresholds.
"""

from dataclasses import dataclass
from enum import Enum


class Phase(Enum):
    """User progression phases."""

    PHASE_1 = 1  # Foundation (Days 1-30)
    PHASE_2 = 2  # Development (Days 31-60)
    PHASE_3 = 3  # Integration (Days 61-90)
    MAINTENANCE = 4  # Post-90 day


class Framework(Enum):
    """Speaking structure frameworks."""

    PREP = "PREP"  # Point, Reason, Example, Point
    WHAT_SO_WHAT_NOW_WHAT = "What-So What-Now What"
    PROBLEM_SOLUTION_BENEFIT = "Problem-Solution-Benefit"
    STAR = "STAR"  # Situation, Task, Action, Result
    PYRAMID = "Pyramid Principle"
    PAST_PRESENT_FUTURE = "Past-Present-Future"


@dataclass
class WarmUpExercise:
    """Warm-up exercise configuration."""

    name: str
    instructions: str
    duration_estimate: str  # Human-readable (e.g., "30 seconds")


@dataclass
class PhaseConfig:
    """
    Complete configuration for a practice phase.

    All values match PRD tables (docs/03_tool_prd_v2.md).
    """

    # Phase identification
    phase: Phase
    name: str  # e.g., "Foundation", "Development"
    day_range: str  # e.g., "Days 1-30"
    goals: str  # Primary objectives for this phase

    # Metrics tracked
    active_metrics: list[str]  # Metric names to track this phase

    # Frameworks available
    available_frameworks: list[Framework]

    # Topic configuration
    topic_types: list[str]  # Types of topics for this phase

    # Timing parameters
    prep_time_seconds: int  # Prep time allowed
    speaking_duration_min: int  # Minimum speaking duration (seconds)
    speaking_duration_max: int  # Maximum speaking duration (seconds)

    # Warm-up exercises
    warm_up_exercises: list[WarmUpExercise]

    # Transition thresholds (to advance to next phase)
    min_sessions: int  # Minimum sessions in this phase
    transition_criteria: dict[str, float]  # Metric name -> threshold

    # Focus skills pool
    available_focus_skills: list[str]


# Phase 1: Foundation (Days 1-30)
PHASE_1_CONFIG = PhaseConfig(
    phase=Phase.PHASE_1,
    name="Foundation",
    day_range="Days 1-30",
    goals="Build filler awareness (don't eliminate — just count). Master the PREP framework. Replace fillers with pauses by end of phase.",
    active_metrics=[
        "filler_rate",  # Fillers per minute
        "filler_percentage",  # Fillers as % of total words
        "framework_completion",  # Y/N - did they hit all components
        "subjective_comfort",  # 1-10 self-rating
    ],
    available_frameworks=[
        Framework.PREP,
        Framework.WHAT_SO_WHAT_NOW_WHAT,  # Added in weeks 3-4
    ],
    topic_types=[
        "explain",  # Explain a concept you know well
        "teach",  # Teach something to a non-expert
        "describe",  # Describe a recent decision
    ],
    prep_time_seconds=60,  # 60s weeks 1-2, 30s weeks 3-4 (simplified to 60s)
    speaking_duration_min=60,  # 60 seconds minimum
    speaking_duration_max=90,  # 90 seconds maximum
    warm_up_exercises=[
        WarmUpExercise(
            name="Box Breathing",
            instructions="Box breathing: Inhale 4 counts, hold 4, exhale 4, hold 4. Repeat 3 cycles.",
            duration_estimate="45 seconds",
        ),
        WarmUpExercise(
            name="Lip Trills",
            instructions="Lip trills: Keep lips relaxed and blow air through them while humming. Slide up and down in pitch.",
            duration_estimate="20 seconds",
        ),
        WarmUpExercise(
            name="Tongue Twister",
            instructions='Tongue twister: "Red leather, yellow leather" — say slowly 3x, then fast 3x.',
            duration_estimate="30 seconds",
        ),
        WarmUpExercise(
            name="Read Aloud",
            instructions="Read one sentence aloud slowly, focusing on clear articulation.",
            duration_estimate="15 seconds",
        ),
    ],
    min_sessions=20,
    transition_criteria={
        "filler_rate": 5.0,  # ≤5 fillers/min for last 5 sessions
        "framework_completion": 80.0,  # >80% framework completion rate
    },
    available_focus_skills=[
        "Filler awareness",
        "Framework adherence",
        "Pause replacement",
        "Clear articulation",
    ],
)

# Phase 2: Development (Days 31-60)
PHASE_2_CONFIG = PhaseConfig(
    phase=Phase.PHASE_2,
    name="Development",
    day_range="Days 31-60",
    goals="Vocal variety. Strategic pausing. Framework rotation. Increase topic complexity.",
    active_metrics=[
        # Carry forward from Phase 1
        "filler_rate",
        "filler_percentage",
        "framework_completion",
        "subjective_comfort",
        # New in Phase 2
        "speaking_rate_wpm",  # Words per minute
        "maze_rate",  # False starts / mazes per minute
        "sentence_completion_rate",  # % of complete sentences
    ],
    available_frameworks=[
        Framework.PREP,
        Framework.WHAT_SO_WHAT_NOW_WHAT,
        Framework.PROBLEM_SOLUTION_BENEFIT,
        Framework.PAST_PRESENT_FUTURE,
    ],
    topic_types=[
        "explain",
        "teach",
        "persuade",  # New: persuasive arguments
        "analyze",  # New: trend analysis
        "feynman",  # New: explain to a 5-year-old (no jargon)
    ],
    prep_time_seconds=10,  # Reduced from Phase 1
    speaking_duration_min=120,  # 2 minutes
    speaking_duration_max=180,  # 2 min + 60s "repeat and improve"
    warm_up_exercises=[
        WarmUpExercise(
            name="Diaphragmatic Breathing",
            instructions="Diaphragmatic breathing: Place hand on belly. Breathe deeply so belly expands. 5 deep breaths.",
            duration_estimate="30 seconds",
        ),
        WarmUpExercise(
            name="Vocal Sirens",
            instructions="Vocal sirens: Start at lowest comfortable pitch and slide to highest, then back down. Repeat 3x.",
            duration_estimate="30 seconds",
        ),
        WarmUpExercise(
            name="Speed Tongue Twister",
            instructions='Tongue twister at max clean speed: "Unique New York, you know you need unique New York" — 5x fast.',
            duration_estimate="20 seconds",
        ),
        WarmUpExercise(
            name="Consonant-Vowel Drill",
            instructions='Consonant-vowel drill: "Pa-Ta-Ka" repeated rapidly 10x, focusing on crisp articulation.',
            duration_estimate="20 seconds",
        ),
    ],
    min_sessions=20,
    transition_criteria={
        "filler_rate": 3.0,  # ≤3 fillers/min
        "maze_rate": 2.0,  # <2 mazes/min
        "sentence_completion_rate": 90.0,  # >90% sentence completion
    },
    available_focus_skills=[
        "Filler reduction (active replacement)",
        "Vocal variety",
        "Strategic pausing",
        "Pacing control",
        "Framework rotation",
        "Topic complexity handling",
    ],
)

# Phase 3: Integration (Days 61-90)
PHASE_3_CONFIG = PhaseConfig(
    phase=Phase.PHASE_3,
    name="Integration",
    day_range="Days 61-90",
    goals="Handle zero-prep scenarios. Cognitive flexibility under pressure. Delivery polish.",
    active_metrics=[
        # Carry forward from Phase 2
        "filler_rate",
        "filler_percentage",
        "framework_completion",
        "subjective_comfort",
        "speaking_rate_wpm",
        "maze_rate",
        "sentence_completion_rate",
        # New in Phase 3
        "pause_quality",  # % pauses at syntactic boundaries
        "vocal_variety",  # Subjective rating
        "hedging_frequency",  # Hedging language per minute
        "key_message_delivery",  # Did main point land clearly?
    ],
    available_frameworks=[
        Framework.PREP,
        Framework.WHAT_SO_WHAT_NOW_WHAT,
        Framework.PROBLEM_SOLUTION_BENEFIT,
        Framework.STAR,
        Framework.PYRAMID,
        Framework.PAST_PRESENT_FUTURE,
    ],
    topic_types=[
        "hostile_qa",  # AI-generated challenging questions
        "argue_both_sides",  # 60s FOR / 60s AGAINST
        "story_from_words",  # Story from 3 random words
        "no_prep_speech",  # Zero-prep 3-minute speech (capstone)
        "persuasive_speech",  # Hook → problem → solution → vision → CTA
    ],
    prep_time_seconds=0,  # Zero for capstone exercises
    speaking_duration_min=120,  # 2 minutes minimum
    speaking_duration_max=180,  # 3 minutes maximum
    warm_up_exercises=[
        WarmUpExercise(
            name="Box Breathing (Abbreviated)",
            instructions="Box breathing: 4 cycles only (inhale 4, hold 4, exhale 4, hold 4).",
            duration_estimate="30 seconds",
        ),
        WarmUpExercise(
            name="Speed Tongue Twister",
            instructions='One tongue twister at speed: "She sells seashells by the seashore" — 5x fast.',
            duration_estimate="20 seconds",
        ),
    ],
    min_sessions=30,  # Complete the 90-day arc
    transition_criteria={
        "filler_rate": 2.0,  # ≤2 fillers/min consistently
        "speaking_rate_wpm": 145.0,  # WPM in 130-160 range (using midpoint)
        "hedging_frequency": 1.0,  # Minimal hedging
    },
    available_focus_skills=[
        "Conciseness",
        "Hedging elimination",
        "Cognitive flexibility",
        "Strong openings",
        "Strong closings",
        "Zero-prep confidence",
        "Pressure handling",
    ],
)

# Maintenance phase (post-90 days)
MAINTENANCE_CONFIG = PhaseConfig(
    phase=Phase.MAINTENANCE,
    name="Maintenance",
    day_range="Day 91+",
    goals="Maintain skills. Full exercise rotation. All metrics active.",
    active_metrics=PHASE_3_CONFIG.active_metrics,  # All metrics
    available_frameworks=PHASE_3_CONFIG.available_frameworks,  # All frameworks
    topic_types=PHASE_3_CONFIG.topic_types,  # All topic types
    prep_time_seconds=0,  # User chooses
    speaking_duration_min=120,
    speaking_duration_max=180,
    warm_up_exercises=PHASE_3_CONFIG.warm_up_exercises,
    min_sessions=0,  # No transition from maintenance
    transition_criteria={},  # No further transitions
    available_focus_skills=PHASE_3_CONFIG.available_focus_skills,
)


def get_phase_config(phase: Phase) -> PhaseConfig:
    """
    Get configuration for a specific phase.

    Args:
        phase: Phase enum value

    Returns:
        PhaseConfig for the requested phase

    Raises:
        ValueError: If phase is invalid
    """
    config_map = {
        Phase.PHASE_1: PHASE_1_CONFIG,
        Phase.PHASE_2: PHASE_2_CONFIG,
        Phase.PHASE_3: PHASE_3_CONFIG,
        Phase.MAINTENANCE: MAINTENANCE_CONFIG,
    }

    if phase not in config_map:
        raise ValueError(f"Invalid phase: {phase}")

    return config_map[phase]


def get_framework_components(framework: Framework) -> list[str]:
    """
    Get the structural components for a framework.

    Args:
        framework: Framework enum value

    Returns:
        List of component names for display

    Examples:
        >>> get_framework_components(Framework.PREP)
        ['Point', 'Reason', 'Example', 'Point (restate)']
    """
    components = {
        Framework.PREP: [
            "Point (main message)",
            "Reason (why it matters)",
            "Example (evidence or story)",
            "Point (restate with clarity)",
        ],
        Framework.WHAT_SO_WHAT_NOW_WHAT: [
            "What (the situation or fact)",
            "So What (why it matters)",
            "Now What (action or implication)",
        ],
        Framework.PROBLEM_SOLUTION_BENEFIT: [
            "Problem (what's wrong)",
            "Solution (how to fix it)",
            "Benefit (why this solution wins)",
        ],
        Framework.STAR: [
            "Situation (context)",
            "Task (what needed to be done)",
            "Action (what you did)",
            "Result (outcome)",
        ],
        Framework.PYRAMID: [
            "Main Point (upfront)",
            "Supporting Arguments (3 max)",
            "Evidence (for each argument)",
        ],
        Framework.PAST_PRESENT_FUTURE: [
            "Past (what happened)",
            "Present (current situation)",
            "Future (what's next)",
        ],
    }

    return components.get(framework, [])
