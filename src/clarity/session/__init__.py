"""
Session setup and phase management for MVP1.

Implements phase-aware session configuration, topic rotation, framework
assignment, and warm-up exercises.
"""

from clarity.session.baseline import (
    BaselineSessionBrief,
    get_baseline_metrics,
    has_baseline,
    setup_baseline_session,
    store_baseline_metrics,
)
from clarity.session.focus_skills import get_skill_description, select_focus_skills
from clarity.session.framework_assignment import assign_framework
from clarity.session.phase_config import (
    Framework,
    Phase,
    PhaseConfig,
    WarmUpExercise,
    get_framework_components,
    get_phase_config,
)
from clarity.session.setup import (
    SessionBrief,
    check_phase_transition,
    detect_current_phase,
    is_baseline_session,
    setup_session,
)
from clarity.session.topics import Topic, TopicManager, parse_custom_topic
from clarity.session.warmup import display_warmup_exercises, display_warmup_summary

__all__ = [
    # Phase configuration
    "Phase",
    "PhaseConfig",
    "Framework",
    "WarmUpExercise",
    "get_phase_config",
    "get_framework_components",
    # Topics
    "Topic",
    "TopicManager",
    "parse_custom_topic",
    # Framework assignment
    "assign_framework",
    # Focus skills
    "select_focus_skills",
    "get_skill_description",
    # Warm-up
    "display_warmup_exercises",
    "display_warmup_summary",
    # Session setup
    "SessionBrief",
    "setup_session",
    "detect_current_phase",
    "check_phase_transition",
    "is_baseline_session",
    # Baseline
    "BaselineSessionBrief",
    "setup_baseline_session",
    "has_baseline",
    "store_baseline_metrics",
    "get_baseline_metrics",
]
