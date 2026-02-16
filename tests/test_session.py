"""
Tests for session setup and phase management (Epic 1.3).

Tests phase configuration, topic rotation, framework assignment,
focus skill selection, and session orchestration.
"""

import tempfile
from pathlib import Path

import pytest

from clarity.session import (
    Framework,
    Phase,
    Topic,
    TopicManager,
    assign_framework,
    detect_current_phase,
    get_baseline_metrics,
    get_framework_components,
    get_phase_config,
    get_skill_description,
    has_baseline,
    is_baseline_session,
    parse_custom_topic,
    select_focus_skills,
    store_baseline_metrics,
)
from clarity.storage import StorageManager


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / ".clarity"
        storage = StorageManager(storage_dir)
        storage.init_storage()
        yield storage


# ===== Phase Configuration Tests =====


def test_phase_enum():
    """Test Phase enum values."""
    assert Phase.PHASE_1.value == 1
    assert Phase.PHASE_2.value == 2
    assert Phase.PHASE_3.value == 3
    assert Phase.MAINTENANCE.value == 4


def test_framework_enum():
    """Test Framework enum values."""
    assert Framework.PREP.value == "PREP"
    assert Framework.STAR.value == "STAR"
    assert Framework.PYRAMID.value == "Pyramid Principle"


def test_get_phase_config_phase1():
    """Test retrieving Phase 1 configuration."""
    config = get_phase_config(Phase.PHASE_1)

    assert config.phase == Phase.PHASE_1
    assert config.name == "Foundation"
    assert "filler_rate" in config.active_metrics
    assert Framework.PREP in config.available_frameworks
    assert config.prep_time_seconds == 60
    assert config.speaking_duration_min == 60
    assert config.speaking_duration_max == 90
    assert len(config.warm_up_exercises) > 0


def test_get_phase_config_phase2():
    """Test retrieving Phase 2 configuration."""
    config = get_phase_config(Phase.PHASE_2)

    assert config.phase == Phase.PHASE_2
    assert config.name == "Development"
    assert "maze_rate" in config.active_metrics  # New in Phase 2
    assert config.prep_time_seconds == 10  # Reduced from Phase 1
    assert config.speaking_duration_min == 120  # 2 minutes


def test_get_phase_config_phase3():
    """Test retrieving Phase 3 configuration."""
    config = get_phase_config(Phase.PHASE_3)

    assert config.phase == Phase.PHASE_3
    assert config.name == "Integration"
    assert "hedging_frequency" in config.active_metrics  # New in Phase 3
    assert config.prep_time_seconds == 0  # Zero prep


def test_get_framework_components():
    """Test framework component retrieval."""
    components = get_framework_components(Framework.PREP)

    assert len(components) == 4
    assert any("Point" in c for c in components)
    assert any("Reason" in c for c in components)
    assert any("Example" in c for c in components)


def test_get_framework_components_star():
    """Test STAR framework components."""
    components = get_framework_components(Framework.STAR)

    assert len(components) == 4
    assert any("Situation" in c for c in components)
    assert any("Task" in c for c in components)
    assert any("Action" in c for c in components)
    assert any("Result" in c for c in components)


# ===== Topic Management Tests =====


def test_topic_dataclass():
    """Test Topic dataclass structure."""
    topic = Topic("Test Title", "Test description", "explain", 1)

    assert topic.title == "Test Title"
    assert topic.description == "Test description"
    assert topic.topic_type == "explain"
    assert topic.topic_id == 1


def test_topic_manager_get_topic(temp_storage):
    """Test topic selection."""
    manager = TopicManager(temp_storage)
    topic = manager.get_topic()

    assert isinstance(topic, Topic)
    assert topic.topic_id > 0  # Valid ID
    assert topic.title != ""
    assert topic.topic_type in ["explain", "teach", "persuade", "analyze", "describe"]


def test_topic_manager_no_repeats_until_exhausted(temp_storage):
    """Test that topics don't repeat until pool is exhausted."""
    manager = TopicManager(temp_storage)

    # Get 5 topics
    topics = [manager.get_topic() for _ in range(5)]
    topic_ids = [t.topic_id for t in topics]

    # All should be unique
    assert len(set(topic_ids)) == 5


def test_topic_manager_override(temp_storage):
    """Test manual topic override."""
    manager = TopicManager(temp_storage)
    topic = manager.get_topic(override_title="Custom Topic About AI")

    assert topic.title == "Custom Topic About AI"
    assert topic.topic_type == "custom"
    assert topic.topic_id == -1  # Special ID for custom


def test_topic_manager_filter_by_type(temp_storage):
    """Test filtering topics by type."""
    manager = TopicManager(temp_storage)
    topic = manager.get_topic(allowed_types=["explain"])

    assert topic.topic_type == "explain"


def test_topic_manager_rotation_stats(temp_storage):
    """Test rotation statistics."""
    manager = TopicManager(temp_storage)

    # Initial stats
    stats = manager.get_rotation_stats()
    assert stats["topics_used"] == 0
    assert stats["rotation_count"] == 0

    # Use a topic
    manager.get_topic()

    # Updated stats
    stats = manager.get_rotation_stats()
    assert stats["topics_used"] == 1


def test_parse_custom_topic():
    """Test parsing custom topic from user input."""
    topic = parse_custom_topic("The future of remote work")

    assert topic.title == "The future of remote work"
    assert topic.topic_type == "custom"
    assert topic.topic_id == -1


def test_parse_custom_topic_long():
    """Test parsing very long custom topic."""
    long_text = "A" * 200
    topic = parse_custom_topic(long_text)

    assert len(topic.title) <= 100  # Truncated
    assert topic.title.endswith("...")


# ===== Framework Assignment Tests =====


def test_assign_framework_returns_prep():
    """Test framework assignment (MVP1: all PREP)."""
    topic = Topic("Test", "Description", "explain", 1)
    framework = assign_framework(topic, [Framework.PREP])

    assert framework == Framework.PREP


def test_assign_framework_with_multiple_available():
    """Test framework assignment with multiple options."""
    topic = Topic("Test", "Description", "persuade", 2)
    frameworks = [Framework.PREP, Framework.PROBLEM_SOLUTION_BENEFIT]
    framework = assign_framework(topic, frameworks)

    # MVP1: Still returns PREP regardless of available frameworks
    assert framework == Framework.PREP


# ===== Focus Skills Tests =====


def test_select_focus_skills_no_history(temp_storage):
    """Test focus skill selection with no session history."""
    config = get_phase_config(Phase.PHASE_1)
    skills = select_focus_skills(config, temp_storage, num_skills=2)

    assert len(skills) == 2
    assert all(skill in config.available_focus_skills for skill in skills)


def test_select_focus_skills_with_history(temp_storage):
    """Test focus skill selection with session history."""
    # Add session data with metrics
    temp_storage.append_session(
        {
            "topic": "Test",
            "phase": "PHASE_1",
            "metrics": {
                "filler_rate": 8.5,  # High - needs improvement
                "framework_completion": 60,  # Low - needs improvement
            },
        }
    )

    config = get_phase_config(Phase.PHASE_1)
    skills = select_focus_skills(config, temp_storage, num_skills=2)

    assert len(skills) == 2
    # Skills should be from phase-appropriate pool
    assert all(skill in config.available_focus_skills for skill in skills)


def test_get_skill_description():
    """Test skill description retrieval."""
    desc = get_skill_description("Filler awareness")

    assert len(desc) > 0
    assert "filler" in desc.lower()


def test_get_skill_description_unknown():
    """Test skill description for unknown skill."""
    desc = get_skill_description("Unknown Skill")

    assert "Focus on this skill" in desc


# ===== Phase Detection Tests =====


def test_detect_current_phase_no_sessions(temp_storage):
    """Test phase detection with no sessions."""
    phase = detect_current_phase(temp_storage)

    assert phase == Phase.PHASE_1


def test_detect_current_phase_from_storage(temp_storage):
    """Test phase detection from stored profile."""
    # Set phase in profile
    data = temp_storage.read_all()
    if "profile" not in data:
        data["profile"] = {}
    data["profile"]["current_phase"] = "PHASE_2"
    temp_storage._atomic_write(temp_storage.sessions_file, data)

    phase = detect_current_phase(temp_storage)

    assert phase == Phase.PHASE_2


# ===== Baseline Session Tests =====


def test_is_baseline_session_true(temp_storage):
    """Test baseline detection for first session."""
    assert is_baseline_session(temp_storage) is True


def test_is_baseline_session_false(temp_storage):
    """Test baseline detection after sessions exist."""
    temp_storage.append_session({"topic": "Test", "metrics": {}})

    assert is_baseline_session(temp_storage) is False


def test_has_baseline_false(temp_storage):
    """Test baseline check when not completed."""
    assert has_baseline(temp_storage) is False


def test_store_and_retrieve_baseline_metrics(temp_storage):
    """Test storing and retrieving baseline metrics."""
    metrics = {
        "filler_rate": 8.5,
        "filler_percentage": 4.2,
        "framework_completion": 60,
    }

    store_baseline_metrics(temp_storage, metrics)

    assert has_baseline(temp_storage) is True
    retrieved = get_baseline_metrics(temp_storage)
    assert retrieved == metrics


def test_get_baseline_metrics_none(temp_storage):
    """Test baseline metrics retrieval when none exist."""
    metrics = get_baseline_metrics(temp_storage)

    assert metrics is None


# ===== Integration Tests =====


def test_full_topic_rotation_cycle(temp_storage):
    """Test complete rotation through topic pool."""
    manager = TopicManager(temp_storage)

    # Track initial pool size
    initial_stats = manager.get_rotation_stats()
    pool_size = initial_stats["topics_remaining"] + initial_stats["topics_used"]

    # Use all topics in pool
    used_ids = set()
    for _ in range(pool_size):
        topic = manager.get_topic()
        used_ids.add(topic.topic_id)

    # All topics should have been used
    assert len(used_ids) == pool_size

    # After exhausting pool, next topic should start new rotation
    # (Implementation resets used_ids when pool exhausted)


def test_phase_config_consistency():
    """Test that all phases have consistent structure."""
    phases = [Phase.PHASE_1, Phase.PHASE_2, Phase.PHASE_3, Phase.MAINTENANCE]

    for phase in phases:
        config = get_phase_config(phase)

        assert config.phase == phase
        assert len(config.name) > 0
        assert len(config.active_metrics) > 0
        assert len(config.available_frameworks) > 0
        assert len(config.available_focus_skills) > 0
        assert config.speaking_duration_min > 0
        assert config.speaking_duration_max >= config.speaking_duration_min


def test_phase_progression_metrics():
    """Test that metrics expand across phases."""
    phase1 = get_phase_config(Phase.PHASE_1)
    phase2 = get_phase_config(Phase.PHASE_2)
    phase3 = get_phase_config(Phase.PHASE_3)

    # Phase 2 should have all Phase 1 metrics + new ones
    phase1_metrics = set(phase1.active_metrics)
    phase2_metrics = set(phase2.active_metrics)
    assert phase1_metrics.issubset(phase2_metrics)

    # Phase 3 should have all Phase 2 metrics + new ones
    phase3_metrics = set(phase3.active_metrics)
    assert phase2_metrics.issubset(phase3_metrics)


def test_framework_availability_progression():
    """Test that frameworks expand across phases."""
    phase1 = get_phase_config(Phase.PHASE_1)
    phase2 = get_phase_config(Phase.PHASE_2)
    phase3 = get_phase_config(Phase.PHASE_3)

    # Phase 1 should have fewer frameworks than Phase 3
    assert len(phase1.available_frameworks) <= len(phase3.available_frameworks)

    # PREP should be available in all phases
    assert Framework.PREP in phase1.available_frameworks
    assert Framework.PREP in phase2.available_frameworks
    assert Framework.PREP in phase3.available_frameworks
